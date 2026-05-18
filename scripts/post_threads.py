import json
import mimetypes
import os
import sys
import time
from pathlib import Path
from uuid import uuid4

import requests
from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

USER_ID = os.getenv("THREADS_USER_ID")
ACCESS_TOKEN = os.getenv("THREADS_ACCESS_TOKEN")
BASE_URL = "https://graph.threads.net/v1.0"

AWS_REGION = os.getenv("AWS_REGION")
S3_BUCKET = os.getenv("S3_BUCKET")
S3_PUBLIC_BASE_URL = os.getenv("S3_PUBLIC_BASE_URL")


def redact_token(text: str) -> str:
    if ACCESS_TOKEN and ACCESS_TOKEN in text:
        return text.replace(ACCESS_TOKEN, "<redacted-access-token>")
    return text


def posts_need_s3(posts: list[dict]) -> bool:
    """Return True if any post requires uploading a local image to S3."""
    for post in posts:
        media_type = post.get("media_type", "TEXT").upper()
        if media_type == "IMAGE":
            if not post.get("image_url") and post.get("local_image_path"):
                return True
        elif media_type == "CAROUSEL":
            if post.get("local_image_paths") and not post.get("image_urls"):
                return True
    return False


def assert_env(posts: list[dict]) -> None:
    required = {
        "THREADS_USER_ID": USER_ID,
        "THREADS_ACCESS_TOKEN": ACCESS_TOKEN,
    }

    if posts_need_s3(posts):
        required.update(
            {
                "AWS_REGION": AWS_REGION,
                "S3_BUCKET": S3_BUCKET,
                "S3_PUBLIC_BASE_URL": S3_PUBLIC_BASE_URL,
            }
        )

    missing = [key for key, value in required.items() if not value]

    if missing:
        raise RuntimeError(f"Missing env values: {', '.join(missing)}")


def normalize_topic_tag(topic_tag: str | None) -> str | None:
    if not topic_tag:
        return None

    topic_tag = topic_tag.strip()

    if not topic_tag:
        return None

    if topic_tag.startswith("#"):
        topic_tag = topic_tag.lstrip("#").strip()

    topic_tag = topic_tag.replace(".", " ").replace("&", " ")
    topic_tag = " ".join(topic_tag.split())

    if len(topic_tag) > 50:
        topic_tag = topic_tag[:50].strip()

    return topic_tag or None


def apply_topic_tag(data: dict, post: dict) -> None:
    topic_tag = normalize_topic_tag(post.get("topic_tag"))

    if topic_tag:
        data["topic_tag"] = topic_tag


def upload_local_file_to_s3(local_path: str) -> str:
    # Lazy import: boto3 is only needed when actually uploading.
    import boto3

    path = ROOT / local_path

    if not path.exists():
        raise RuntimeError(f"Local file not found: {path}")

    content_type, _ = mimetypes.guess_type(path.name)
    content_type = content_type or "application/octet-stream"

    key = f"threads-assets/{uuid4().hex}-{path.name}"

    s3 = boto3.client("s3", region_name=AWS_REGION)

    s3.upload_file(
        str(path),
        S3_BUCKET,
        key,
        ExtraArgs={
            "ContentType": content_type,
        },
    )

    return f"{S3_PUBLIC_BASE_URL}/{key}"


def post_to_threads(data: dict) -> dict:
    response = requests.post(
        f"{BASE_URL}/{USER_ID}/threads",
        data=data,
        timeout=60,
    )

    try:
        response.raise_for_status()
    except requests.HTTPError as error:
        raise RuntimeError(f"Create container failed: {redact_token(response.text)}") from error

    return response.json()


def publish_container(container_id: str) -> str:
    data = {
        "creation_id": container_id,
        "access_token": ACCESS_TOKEN,
    }

    response = requests.post(
        f"{BASE_URL}/{USER_ID}/threads_publish",
        data=data,
        timeout=60,
    )

    try:
        response.raise_for_status()
    except requests.HTTPError as error:
        raise RuntimeError(f"Publish failed: {redact_token(response.text)}") from error

    payload = response.json()

    if "id" not in payload:
        raise RuntimeError(f"Publish failed: {payload}")

    return payload["id"]


def create_text_container(post: dict, reply_to_id: str | None = None) -> str:
    text = post.get("text", "")

    if not text:
        raise RuntimeError("TEXT post requires text")

    data = {
        "media_type": "TEXT",
        "text": text,
        "access_token": ACCESS_TOKEN,
    }

    apply_topic_tag(data, post)

    if reply_to_id:
        data["reply_to_id"] = reply_to_id

    payload = post_to_threads(data)

    if "id" not in payload:
        raise RuntimeError(f"TEXT container creation failed: {payload}")

    return payload["id"]


def create_image_container(post: dict, reply_to_id: str | None = None) -> str:
    text = post.get("text", "")

    image_url = post.get("image_url")

    if not image_url:
        local_image_path = post.get("local_image_path")
        if not local_image_path:
            raise RuntimeError("IMAGE post requires image_url or local_image_path")

        image_url = upload_local_file_to_s3(local_image_path)
        print(f"Uploaded image to S3: {image_url}")

    data = {
        "media_type": "IMAGE",
        "image_url": image_url,
        "access_token": ACCESS_TOKEN,
    }

    if text:
        data["text"] = text

    apply_topic_tag(data, post)

    if reply_to_id:
        data["reply_to_id"] = reply_to_id

    payload = post_to_threads(data)

    if "id" not in payload:
        raise RuntimeError(f"IMAGE container creation failed: {payload}")

    return payload["id"]


def create_carousel_item_container(image_path_or_url: str) -> str:
    if image_path_or_url.startswith("http://") or image_path_or_url.startswith("https://"):
        image_url = image_path_or_url
    else:
        image_url = upload_local_file_to_s3(image_path_or_url)
        print(f"Uploaded carousel image to S3: {image_url}")

    data = {
        "media_type": "IMAGE",
        "image_url": image_url,
        "is_carousel_item": "true",
        "access_token": ACCESS_TOKEN,
    }

    payload = post_to_threads(data)

    if "id" not in payload:
        raise RuntimeError(f"Carousel item container creation failed: {payload}")

    return payload["id"]


def create_carousel_container(post: dict, reply_to_id: str | None = None) -> str:
    text = post.get("text", "")

    image_sources = post.get("image_urls") or post.get("local_image_paths")

    if not image_sources:
        raise RuntimeError("CAROUSEL post requires image_urls or local_image_paths")

    if len(image_sources) < 2:
        raise RuntimeError("CAROUSEL requires at least 2 images")

    item_container_ids = []

    for idx, image_source in enumerate(image_sources, start=1):
        print(f"Creating carousel item {idx}/{len(image_sources)}...")
        item_id = create_carousel_item_container(image_source)
        item_container_ids.append(item_id)
        time.sleep(3)

    data = {
        "media_type": "CAROUSEL",
        "children": ",".join(item_container_ids),
        "access_token": ACCESS_TOKEN,
    }

    if text:
        data["text"] = text

    apply_topic_tag(data, post)

    if reply_to_id:
        data["reply_to_id"] = reply_to_id

    payload = post_to_threads(data)

    if "id" not in payload:
        raise RuntimeError(f"CAROUSEL container creation failed: {payload}")

    return payload["id"]


def create_container(post: dict, reply_to_id: str | None = None) -> str:
    media_type = post.get("media_type", "TEXT").upper()

    if media_type == "TEXT":
        return create_text_container(post, reply_to_id)

    if media_type == "IMAGE":
        return create_image_container(post, reply_to_id)

    if media_type == "CAROUSEL":
        return create_carousel_container(post, reply_to_id)

    raise RuntimeError(f"Unsupported media_type: {media_type}")


def load_posts(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    posts = data.get("posts", [])

    if not posts:
        raise RuntimeError("No posts found in draft JSON")

    for idx, post in enumerate(posts, start=1):
        text = post.get("text", "")

        if len(text) > 500:
            raise RuntimeError(f"Post {idx} is too long: {len(text)} characters")

        media_type = post.get("media_type", "TEXT").upper()

        if media_type == "TEXT":
            if not text:
                raise RuntimeError(f"Post {idx} is TEXT but missing text")

        if media_type == "IMAGE":
            if not post.get("image_url") and not post.get("local_image_path"):
                raise RuntimeError(
                    f"Post {idx} is IMAGE but missing image_url/local_image_path"
                )

        if media_type == "CAROUSEL":
            image_sources = post.get("image_urls") or post.get("local_image_paths")
            if not image_sources:
                raise RuntimeError(
                    f"Post {idx} is CAROUSEL but missing image_urls/local_image_paths"
                )
            if len(image_sources) < 2:
                raise RuntimeError(f"Post {idx} is CAROUSEL but has fewer than 2 images")

    return posts


def main():
    draft_path = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else ROOT / "output" / "threads_draft.json"
    )

    posts = load_posts(draft_path)
    assert_env(posts)

    previous_post_id = None
    published = []

    for idx, post in enumerate(posts, start=1):
        media_type = post.get("media_type", "TEXT").upper()
        topic_tag = normalize_topic_tag(post.get("topic_tag"))

        print(f"Creating container for post {idx}/{len(posts)} ({media_type})...")

        if topic_tag:
            print(f"Using topic_tag: {topic_tag}")

        container_id = create_container(post, reply_to_id=previous_post_id)

        time.sleep(8)

        print(f"Publishing post {idx}/{len(posts)}...")

        post_id = publish_container(container_id)

        published.append(
            {
                "index": idx,
                "post_id": post_id,
                "media_type": media_type,
                "topic_tag": topic_tag,
            }
        )

        previous_post_id = post_id

        print(f"Published post {idx}: {post_id}")

        time.sleep(5)

    result_path = ROOT / "output" / "published_result.json"

    with result_path.open("w", encoding="utf-8") as file:
        json.dump({"published": published}, file, ensure_ascii=False, indent=2)

    print(f"Done. Result saved to {result_path}")


if __name__ == "__main__":
    main()
