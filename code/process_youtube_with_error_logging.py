import subprocess
import json
from pathlib import Path
from datetime import timedelta
import re

# ------------------------------------
# CONFIG
# ------------------------------------

CHANNELS = {
    "masterchefnambie": "https://www.youtube.com/@Masterchefnambie",
    "delhifoodwalks": "https://www.youtube.com/@delhifoodwalks",
    "northeastindiafood": "https://www.youtube.com/c/Northeastindiafood",
    "roohi_haflongbar": "https://www.youtube.com/@roohi_haflongbar",
    "main_bhi_bharat": "https://www.youtube.com/c/MainBhiBharat"
}

BASE_DIR = Path("data")

LANG_MAP = {
    "hi": "hindi",
    "en": "english",
    "as": "assamese",
    "bn": "bengali",
    "mr": "marathi",
    "ta": "tamil",
    "te": "telugu",
    "ml": "malayalam",
    "kn": "kannada",
    "pa": "punjabi",
    "or": "odia"
}

# ------------------------------------
# UTILITIES
# ------------------------------------


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


def extract_clean_error(stderr_text):

    for line in stderr_text.splitlines():
        if "ERROR:" in line:
            return line.replace("ERROR:", "").strip()

    lines = [l.strip() for l in stderr_text.splitlines() if l.strip()]
    if lines:
        return lines[-1]

    return "Unknown error"


def format_publish_date(date_str):
    if not date_str or len(date_str) != 8:
        return None
    return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"


def format_duration(seconds):

    if seconds is None:
        return None

    seconds = int(seconds)

    if seconds < 3600:
        return f"{seconds//60:02}:{seconds % 60:02}"
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

    return " ".join(title.split()[:6])


def count_existing_errors(channel_dir):

    return sum(1 for f in channel_dir.glob("errors_*.txt"))


# ------------------------------------
# MAIN PER-CHANNEL PROCESSOR
# ------------------------------------

def process_channel(channel_name):

    print(f"\n===== Processing Channel: {channel_name} =====")

    channel_dir = BASE_DIR / channel_name

    id_files = list(channel_dir.glob("video_ids_*.txt"))

    if not id_files:
        print("❌ No video_ids file found.")
        return

    id_file = id_files[0]

    with open(id_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    updated_lines = lines.copy()

    error_count = count_existing_errors(channel_dir)
    error_file = channel_dir / f"errors.txt"

    if not error_file.exists():
        with open(error_file, "w", encoding="utf-8") as f:
            f.write("Sl. No. | Video_id | Error\n")

    for idx, raw_line in enumerate(lines):

        sl_no = idx + 1
        line = raw_line.strip()

        if not line:
            continue

        if line.endswith(" 1") or line.endswith(" e"):
            continue

        video_id = line

        print(f"\n[{sl_no}] Processing {video_id}")

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
                "ingredients_detected": []
            }

            output = {
                "metadata": metadata,
                transcription_key: []
            }

            out_path = channel_dir / filename

            with open(out_path, "w", encoding="utf-8") as jf:
                json.dump(output, jf, indent=2, ensure_ascii=False)

            updated_lines[idx] = video_id + " 1\n"

            with open(id_file, "w", encoding="utf-8") as f:
                f.writelines(updated_lines)

            print(f"   ✅ Saved {filename}")

        except Exception as e:

            raw_err = str(e)
            clean_err = extract_clean_error(raw_err)

            error_count += 1

            with open(error_file, "a", encoding="utf-8") as ef:
                ef.write(f"{sl_no} | {video_id} | {clean_err}\n")

            updated_lines[idx] = video_id + " e\n"

            with open(id_file, "w", encoding="utf-8") as f:
                f.writelines(updated_lines)

            print(f"   ❌ ERROR logged: {clean_err}")
    
    # rename the error file to include count
    new_error_file = channel_dir / f"errors_{error_count}.txt"
    error_file.rename(new_error_file)
    print(f"\nTotal errors for {channel_name}: {error_count} (logged in {new_error_file.name})")


# ------------------------------------
# ENTRYPOINT
# ------------------------------------

if __name__ == "__main__":

    BASE_DIR.mkdir(exist_ok=True)

    for channel in CHANNELS:
        process_channel(channel)

    print("\n===== RUN COMPLETE =====")
