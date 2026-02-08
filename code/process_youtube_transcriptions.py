import subprocess
import json
import re
import time
from pathlib import Path

BASE_DIR = Path("data")

NODE_PATH = r"C:\Software\node-v22.14.0-win-x64\node.exe"

SLEEP_SECONDS = 4

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

# --------------------------------------------------
# yt-dlp helpers (WITH NODE)
# --------------------------------------------------


def yt_cmd_base():
    return [
        "yt-dlp",
        "--js-runtimes", f'node:"{NODE_PATH}"',
        "--sleep-interval", str(SLEEP_SECONDS),
        "--max-sleep-interval", str(SLEEP_SECONDS + 3)
    ]


def run_yt_dlp_json(video_id):

    url = f"https://www.youtube.com/watch?v={video_id}"

    cmd = yt_cmd_base() + ["-j", url]

    res = subprocess.run(cmd, capture_output=True, text=True)

    if res.returncode != 0:
        raise RuntimeError(res.stderr)

    return json.loads(res.stdout)


def download_and_parse(video_id, lang_code, out_dir):

    # wipe folder BEFORE each attempt
    for f in out_dir.glob("*.vtt"):
        f.unlink()

    url = f"https://www.youtube.com/watch?v={video_id}"

    cmd = yt_cmd_base() + [
        "--skip-download",
        "--write-sub",
        "--write-auto-sub",
        "--sub-lang", lang_code,
        "--sub-format", "vtt",
        "--paths", str(out_dir),
        url
    ]

    subprocess.run(cmd, capture_output=True, text=True)

    files = list(out_dir.glob("*.vtt"))

    if not files:
        return None

    return parse_vtt(files[0])


# --------------------------------------------------
# VTT PARSER
# --------------------------------------------------

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


# --------------------------------------------------
# PER VIDEO LOGIC
# --------------------------------------------------

def process_video(channel_dir, id_file, idx, video_id):

    sl_no = idx + 1

    json_files = list(channel_dir.glob(f"{sl_no}. *.json"))

    if not json_files:
        print(f"❌ Missing JSON for SL {sl_no}")
        return False

    json_path = json_files[0]

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    meta = data["metadata"]

    orig_lang = meta["original_audio_language"]

    orig_code = None
    for k, v in LANG_MAP.items():
        if v == orig_lang:
            orig_code = k

    if not orig_code and orig_lang == "english":
        orig_code = "en"

    # -------------------
    # remove existing transcription keys
    # -------------------

    for k in list(data.keys()):
        if k.startswith("transcription_"):
            del data[k]

    # -------------------
    # yt-dlp inspect
    # -------------------

    raw = run_yt_dlp_json(video_id)

    subs = raw.get("subtitles", {})
    auto = raw.get("automatic_captions", {})

    available = set(subs.keys()) | set(auto.keys())

    out_dir = channel_dir / "_subs_tmp"
    out_dir.mkdir(exist_ok=True)

    def choose_lang(prefix):

        # creator first
        if prefix in subs:
            return prefix

        # auto / translated fallback
        for k in available:
            if k.startswith(prefix):
                return k

        return None

    # -------------------
    # ENGLISH ORIGINAL
    # -------------------

    if orig_lang == "english":

        chosen = choose_lang("en")

        if chosen:
            print("   ▶ English subs:", chosen)

            parsed = download_and_parse(video_id, chosen, out_dir)

            if parsed:
                data["transcription_english"] = parsed
            else:
                print("   ⚠ English subs failed")

    # -------------------
    # NON-ENGLISH ORIGINAL
    # -------------------

    else:

        # original language
        chosen_orig = choose_lang(orig_code)

        if chosen_orig:
            print("   ▶ Original subs:", chosen_orig)

            parsed = download_and_parse(video_id, chosen_orig, out_dir)

            if parsed:
                data[f"transcription_{orig_lang}"] = parsed
            else:
                print("   ⚠ Original language subs failed")

        # english translation
        chosen_en = choose_lang("en")

        if chosen_en:
            print("   ▶ English subs:", chosen_en)

            parsed = download_and_parse(video_id, chosen_en, out_dir)

            if parsed:
                data["transcription_english"] = parsed
            else:
                print("   ⚠ English subs unavailable")

    # cleanup temp
    for f in out_dir.glob("*.vtt"):
        f.unlink()

    # save JSON
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    # -------------------
    # update ID file
    # -------------------

    with open(id_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    lines[idx] = video_id + " 1 1\n"

    with open(id_file, "w", encoding="utf-8") as f:
        f.writelines(lines)

    return True


# --------------------------------------------------
# CHANNEL LOOP
# --------------------------------------------------

def process_channel(channel_dir):

    id_files = list(channel_dir.glob("video_ids_*.txt"))

    if not id_files:
        return

    id_file = id_files[0]

    with open(id_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for idx, raw in enumerate(lines):

        line = raw.strip()

        if not line.endswith(" 1"):
            continue

        video_id = line[:-2]

        print(f"\n▶ Transcribing {channel_dir.name} SL {idx+1} {video_id}")

        try:
            ok = process_video(channel_dir, id_file, idx, video_id)

            if ok:
                print("   ✅ Transcription done")

        except Exception as e:
            print("   ❌ FAILED:", e)


# --------------------------------------------------
# ENTRY
# --------------------------------------------------

if __name__ == "__main__":

    for channel_dir in BASE_DIR.iterdir():
        if channel_dir.is_dir():
            process_channel(channel_dir)

    print("\n===== TRANSCRIPTION STAGE COMPLETE =====")
