import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ZMEDIUM_OUTPUT = ROOT / "output" / "zmediumtomarkdown"
THREADS_DRAFT = ROOT / "output" / "threads_draft.json"
PUBLISHED_RESULT = ROOT / "output" / "published_result.json"
ARTICLE_MD = ROOT / "drafts" / "article.md"


def run(command: list[str]) -> None:
    print(f"Running: {' '.join(command)}")
    subprocess.run(command, cwd=ROOT, check=True)


def cleanup() -> None:
    if ZMEDIUM_OUTPUT.exists():
        shutil.rmtree(ZMEDIUM_OUTPUT)
        print(f"Removed: {ZMEDIUM_OUTPUT}")

    for path in [THREADS_DRAFT, PUBLISHED_RESULT, ARTICLE_MD]:
        if path.exists():
            path.unlink()
            print(f"Removed: {path}")


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit('Usage: python3 scripts/import_medium.py "MEDIUM_URL"')

    medium_url = sys.argv[1]

    cleanup()

    run(["ZMediumToMarkdown", "-p", medium_url])
    run(["python3", "scripts/import_zmedium.py"])

    print("\nDone.")
    print("Next:")
    print("  claude")
    print("  請依照 AGENTS.md，讀取 drafts/article.md，重新產生 output/threads_draft.json。先不要發文。")


if __name__ == "__main__":
    main()
