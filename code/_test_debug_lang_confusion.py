import subprocess
from pathlib import Path
import shutil

VIDEO_ID = "-SkduwWN12o"

BASE = Path("lang_debug")
BASE.mkdir(exist_ok=True)


def wipe():
    for f in BASE.glob("*"):
        f.unlink()


def run(lang):

    wipe()

    url = f"https://www.youtube.com/watch?v={VIDEO_ID}"

    cmd = [
        "yt-dlp",
        "--skip-download",
        "--write-auto-sub",
        "--write-sub",
        "--sub-lang", lang,
        "--sub-format", "vtt",
        "--paths", str(BASE),
        url
    ]

    print("\nRUNNING:", " ".join(cmd))

    p = subprocess.run(cmd, capture_output=True, text=True)

    print("\nSTDERR:\n", p.stderr)

    files = list(BASE.glob("*.vtt"))

    print("\nFILES CREATED:")

    for f in files:
        print(" →", f.name)

        preview = f.read_text(encoding="utf-8")[:300]
        print("   PREVIEW:", preview.replace("\n", " ")[:200])


if __name__ == "__main__":

    print("\n===== REQUESTING HINDI =====")
    run("hi")

    print("\n===== REQUESTING ENGLISH =====")
    run("en")
