import subprocess
import re
from pathlib import Path

VIDEO_ID = "6JyYM4ojHGE"
LANG = "hi"

OUT_DIR = Path("subs_tmp")
OUT_DIR.mkdir(exist_ok=True)


def download_sub(video_id, lang):

    url = f"https://www.youtube.com/watch?v={video_id}"

    cmd = [
        "yt-dlp",
        "--skip-download",
        "--write-auto-sub",
        "--write-sub",
        "--sub-lang", lang,
        "--sub-format", "vtt",
        "--paths", str(OUT_DIR),
        url
    ]

    subprocess.run(cmd, capture_output=True, text=True)

    files = list(OUT_DIR.glob("*.vtt"))

    return files[0] if files else None


def clean_caption_text(text):

    # remove <00:00:01.200> and <c> tags
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

        if not rows:
            continue

        # find timestamp row safely
        ts_row = None
        for r in rows:
            if "-->" in r:
                ts_row = r
                break

        if not ts_row:
            continue

        timestamp = ts_row.split(" --> ")[0]

        # caption lines = everything after timestamp row
        idx = rows.index(ts_row)
        caption_rows = rows[idx + 1:]

        text_parts = []

        for r in caption_rows:
            cleaned = clean_caption_text(r)
            if cleaned:
                text_parts.append(cleaned)

        if not text_parts:
            continue

        final_text = " ".join(text_parts)

        # avoid duplicates
        if final_text in seen:
            continue

        seen.add(final_text)
        lines.append(f"[{timestamp}] {final_text}")

    return lines


    lines = []

    content = path.read_text(encoding="utf-8")

    blocks = content.split("\n\n")

    seen = set()

    for block in blocks:

        rows = block.splitlines()

        if len(rows) >= 3 and "-->" in rows[0] or "-->" in rows[1]:

            ts_line = rows[0] if "-->" in rows[0] else rows[1]

            timestamp = ts_line.split(" --> ")[0]

            caption_rows = rows[2:] if "-->" in rows[1] else rows[1:]

            text = " ".join(clean_caption_text(r) for r in caption_rows)

            text = text.strip()

            if text and text not in seen:
                seen.add(text)
                lines.append(f"[{timestamp}] {text}")

    return lines


if __name__ == "__main__":

    vtt_file = download_sub(VIDEO_ID, LANG)

    if not vtt_file:
        print("❌ No subtitle file found")
        exit()

    print("Using file:", vtt_file.name)

    parsed = parse_vtt(vtt_file)

    print("\nParsed captions (first 10):\n")

    for line in parsed[:10]:
        print(line)

    print(f"\nTotal lines parsed: {len(parsed)}")
