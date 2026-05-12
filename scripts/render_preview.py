import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    draft_path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "output" / "threads_draft.json"
    preview_path = ROOT / "output" / "preview.md"

    if not draft_path.exists():
        raise SystemExit(f"Draft not found: {draft_path}")

    data = json.loads(draft_path.read_text(encoding="utf-8"))
    posts = data.get("posts", [])

    lines = ["# Threads Preview", ""]

    for post in posts:
        index = post.get("index")
        media_type = post.get("media_type", "TEXT").upper()
        topic_tag = post.get("topic_tag", "")
        text = post.get("text", "")

        lines.append(f"## Post {index} — {media_type}")
        lines.append("")
        lines.append(f"**topic_tag:** {topic_tag}")
        lines.append("")
        lines.append(text)
        lines.append("")

        if media_type == "IMAGE":
            image_path = post.get("local_image_path")
            if image_path:
                lines.append(f"![Post {index}]({image_path})")
                lines.append("")

        if media_type == "CAROUSEL":
            for i, image_path in enumerate(post.get("local_image_paths", []), start=1):
                lines.append(f"![Post {index}-{i}]({image_path})")
                lines.append("")

        lines.append("---")
        lines.append("")

    preview_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Preview written to: {preview_path}")


if __name__ == "__main__":
    main()
