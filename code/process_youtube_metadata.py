import subprocess
import json
from pathlib import Path
from datetime import timedelta
import re
import sys

# ------------------------
# CHANNEL CONFIG
# ------------------------

CHANNELS = {
    "masterchefnambie": "https://www.youtube.com/@Masterchefnambie",
    "delhifoodwalks": "https://www.youtube.com/@delhifoodwalks",
    "northeastindiafood": "https://www.youtube.com/c/Northeastindiafood",
    "roohi_haflongbar": "https://www.youtube.com/@roohi_haflongbar",
    "main_bhi_bharat": "https://www.youtube.com/c/MainBhiBharat"
}

BASE_DIR = Path("data")

# ------------------------
# LANGUAGE MAP
# ------------------------

LANG_MAP = {
    "hi": "hindi",
    "en": "english",
    "as": "assamese",
    "bn": "bengali",
    "gu": "gujarati",
    "mr": "marathi",
    "ta": "tamil",
    "te": "telugu",
    "ml": "malayalam",
    "kn": "kannada",
    "pa": "punjabi",
    "or": "odia"
}


# ------------------------
# UTILITIES
# ------------------------

def run_yt_dlp(video_id):

    url = f"https://www.youtube.com/watch?v={video_id}"

    cmd = ["yt-dlp", "-j", url]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr)

    return json.loads(result.stdout)


def format_publish_date(date_str):
    if not date_str or len(date_str) != 8:
        return None
    return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"


def format_duration(seconds):

    if seconds is None:
        return None

    seconds = int(seconds)

    if seconds < 3600:
        mm = seconds // 60
        ss = seconds % 60
        return f"{mm:02}:{ss:02}"
    else:
        return str(timedelta(seconds=seconds))


def normalize_language(code):

    if not code:
        return "unknown"

    return LANG_MAP.get(code, code)


def safe_filename(text):

    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def first_six_words(title):

    words = title.split()
    return " ".join(words[:6])


# ------------------------
# CORE LOGIC
# ------------------------

def process_channel(channel_name):

    print(f"\n===== Processing Channel: {channel_name} =====")

    channel_dir = BASE_DIR / channel_name
    channel_dir.mkdir(parents=True, exist_ok=True)

    id_file = list(channel_dir.glob("video_ids_*.txt"))

    if not id_file:
        print(f"❌ No ID file found in {channel_dir}")
        return

    id_file = id_file[0]

    with open(id_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    updated_lines = lines.copy()

    for idx, raw_line in enumerate(lines):

        line = raw_line.strip()

        sl_no = idx + 1

        if not line:
            continue

        if line.endswith(" 1"):
            continue

        video_id = line

        print(f"\n[{sl_no}] Processing video: {video_id}")

        try:

            raw = run_yt_dlp(video_id)

            title = raw.get("title") or "untitled"

            six_words = first_six_words(title)
            safe_title = safe_filename(six_words)

            filename = f"{sl_no}. {safe_title}.json"

            publish_date = format_publish_date(raw.get("upload_date"))

            duration = format_duration(raw.get("duration"))

            lang_code = raw.get("language")
            lang_name = normalize_language(lang_code)

            transcription_key = f"transcription_{lang_name}"

            metadata = {
                "title": title,
                "channel_name": raw.get("channel"),
                "publish_date": publish_date,
                "view_count": raw.get("view_count"),
                "like_count": raw.get("like_count"),
                "duration": duration,
                "original_audio_language": lang_name,
                "video_id": raw.get("id"),
                "url": raw.get("webpage_url"),
                "description": raw.get("description"),

                # placeholders
                "ingredients_detected": []
            }

            output = {
                "metadata": metadata,
                transcription_key: []
            }

            out_path = channel_dir / filename

            with open(out_path, "w", encoding="utf-8") as jf:
                json.dump(output, jf, indent=2, ensure_ascii=False)

            print(f"   ✅ Saved: {out_path.name}")

            # mark processed
            updated_lines[idx] = video_id + " 1\n"

            # rewrite file after each success (crash safe)
            with open(id_file, "w", encoding="utf-8") as f:
                f.writelines(updated_lines)

        except Exception as e:

            print(f"   ❌ FAILED at SL {sl_no} for {video_id}")
            print(f"      {e}")

            continue


# ------------------------
# MAIN
# ------------------------

if __name__ == "__main__":

    BASE_DIR.mkdir(exist_ok=True)

    for channel in CHANNELS:
        process_channel(channel)

    print("\n===== ALL CHANNELS FINISHED =====")
