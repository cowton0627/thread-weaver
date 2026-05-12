import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ZMEDIUM_DIR = ROOT / "output" / "zmediumtomarkdown"
DRAFT_PATH = ROOT / "drafts" / "article.md"
ASSETS_DIR = ROOT / "assets"


def find_single_markdown() -> Path:
    md_files = list(ZMEDIUM_DIR.glob("*.md"))

    if not md_files:
        raise RuntimeError(f"No markdown files found in {ZMEDIUM_DIR}")

    if len(md_files) > 1:
        print("Multiple markdown files found:")
        for index, path in enumerate(md_files, start=1):
            print(f"{index}. {path.name}")
        raise RuntimeError("Please keep only one markdown file in output/zmediumtomarkdown for now.")

    return md_files[0]


def copy_assets():
    source_assets = ZMEDIUM_DIR / "assets"

    if not source_assets.exists():
        print("No assets directory found. Skipping assets copy.")
        return

    for child in source_assets.iterdir():
        destination = ASSETS_DIR / child.name

        if destination.exists():
            shutil.rmtree(destination)

        if child.is_dir():
            shutil.copytree(child, destination)
        else:
            shutil.copy2(child, destination)

        print(f"Copied assets: {child} -> {destination}")


def rewrite_image_paths(markdown: str) -> str:
    # ZMediumToMarkdown outputs: assets/<post_id>/<file>
    # drafts/article.md needs: ../assets/<post_id>/<file>
    return re.sub(
        r'(!\[[^\]]*\]\()assets/',
        r'\1../assets/',
        markdown,
    )


def main():
    md_path = find_single_markdown()

    DRAFT_PATH.parent.mkdir(parents=True, exist_ok=True)
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    copy_assets()

    markdown = md_path.read_text(encoding="utf-8")
    markdown = rewrite_image_paths(markdown)

    DRAFT_PATH.write_text(markdown, encoding="utf-8")

    print(f"Imported markdown: {md_path} -> {DRAFT_PATH}")
    print("Done.")


if __name__ == "__main__":
    main()
