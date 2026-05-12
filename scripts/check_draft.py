import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAX_TEXT_LENGTH = 430


def main() -> None:
    draft_path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "output" / "threads_draft.json"

    if not draft_path.exists():
        raise SystemExit(f"Draft not found: {draft_path}")

    data = json.loads(draft_path.read_text(encoding="utf-8"))
    posts = data.get("posts", [])

    if not posts:
        raise SystemExit("No posts found.")

    has_error = False

    for post in posts:
        index = post.get("index")
        media_type = post.get("media_type", "TEXT").upper()
        text = post.get("text", "")
        topic_tag = post.get("topic_tag")

        length_status = "OK" if len(text) <= MAX_TEXT_LENGTH else "OVER"
        print(f"Post {index} ({media_type}): {len(text)} chars [{length_status}]")

        if len(text) > MAX_TEXT_LENGTH:
            has_error = True

        if not topic_tag:
            print("  ⚠ Missing topic_tag")

        if media_type == "IMAGE":
            image_path = post.get("local_image_path")
            if not image_path:
                print("  ❌ Missing local_image_path")
                has_error = True
            elif not (ROOT / image_path).exists():
                print(f"  ❌ Image not found: {image_path}")
                has_error = True
            else:
                print(f"  Image: {image_path}")

        if media_type == "CAROUSEL":
            image_paths = post.get("local_image_paths", [])
            if len(image_paths) < 2:
                print("  ❌ CAROUSEL requires at least 2 images")
                has_error = True

            for image_path in image_paths:
                if not (ROOT / image_path).exists():
                    print(f"  ❌ Image not found: {image_path}")
                    has_error = True
                else:
                    print(f"  Image: {image_path}")

    if has_error:
        raise SystemExit("\nDraft check failed.")

    print("\nDraft check passed.")


if __name__ == "__main__":
    main()
