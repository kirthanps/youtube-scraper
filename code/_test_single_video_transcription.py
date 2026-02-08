import subprocess
import time
import re
from pathlib import Path

VIDEO_ID = "-SkduwWN12o"

SLEEP_SECONDS = 4

TMP_DIR = Path("subs_debug")
TMP_DIR.mkdir(exist_ok=True)


# -----------------------------
# VTT PARSER
# -----------------------------

def clean_caption_text(text):

    text = re.sub(r"<\d\d:\d\d:\d\d\.\d+>", "", text)
    text = re.sub(r"</?c>", "", text)

    return text.strip()


def parse_vtt(path):

    content = path.read_text(encoding="utf-8")

    blocks = content.split("\n\n")

    lines = []
    seen = set()

    for block in blocks:

        rows = [r.strip() for r in block.splitlines() if r.strip()]

        ts_row = None
        for r in rows:
            if "-->" in r:
                ts_row = r
                break

        if not ts_row:
            continue

        timestamp = ts_row.split(" --> ")[0]

        idx = rows.index(ts_row)
        caption_rows = rows[idx + 1:]

        parts = []

        for r in caption_rows:
            cleaned = clean_caption_text(r)
            if cleaned:
                parts.append(cleaned)

        if not parts:
            continue

        final = " ".join(parts)

        if final in seen:
            continue

        seen.add(final)

        lines.append(f"[{timestamp}] {final}")

    return lines


# -----------------------------
# yt-dlp runner
# -----------------------------

def fetch_lang(lang_code):

    # wipe folder before run
    for f in TMP_DIR.glob("*.vtt"):
        f.unlink()

    url = f"https://www.youtube.com/watch?v={VIDEO_ID}"

    cmd = [
        "yt-dlp",
        "--sleep-interval", str(SLEEP_SECONDS),
        "--max-sleep-interval", str(SLEEP_SECONDS + 2),
        "--skip-download",
        "--write-auto-sub",
        "--write-sub",
        "--sub-lang", lang_code,
        "--sub-format", "vtt",
        "--paths", str(TMP_DIR),
        url
    ]

    print("\nRunning:", " ".join(cmd))

    subprocess.run(cmd, capture_output=True, text=True)

    files = list(TMP_DIR.glob("*.vtt"))

    if not files:
        print("⚠ No subtitles downloaded for", lang_code)
        return None

    return parse_vtt(files[0])


# -----------------------------
# MAIN
# -----------------------------

if __name__ == "__main__":

    print("\n===== FETCHING HINDI =====")

    hindi = fetch_lang("hi")

    if hindi:
        print("\n--- HINDI (first 15 lines) ---\n")
        for line in hindi[:15]:
            print(line)

        print("\nTOTAL HINDI LINES:", len(hindi))

    time.sleep(5)

    print("\n===== FETCHING ENGLISH =====")

    english = fetch_lang("en")

    if english:
        print("\n--- ENGLISH (first 15 lines) ---\n")
        for line in english[:15]:
            print(line)

        print("\nTOTAL ENGLISH LINES:", len(english))
