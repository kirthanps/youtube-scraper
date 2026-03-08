import subprocess
import json
import re
from pathlib import Path

# ======================================================
# CONFIG
# ======================================================

BASE_DIR = Path("data")
TMP_DIR_NAME = "_subs_tmp"

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

REVERSE_LANG_MAP = {v: k for k, v in LANG_MAP.items()}

# ======================================================
# yt-dlp helpers
# ======================================================


def run_yt_json(video_id):

    url = f"https://www.youtube.com/watch?v={video_id}"

    cmd = ["yt-dlp", "-j", url]

    p = subprocess.run(cmd, capture_output=True, text=True)

    if p.returncode != 0:
        raise RuntimeError(p.stderr)

    return json.loads(p.stdout)


def download_subs(video_id, lang_code, out_dir):

    out_dir.mkdir(exist_ok=True)

    # wipe before run
    for f in out_dir.glob("*.vtt"):
        f.unlink()

    url = f"https://www.youtube.com/watch?v={video_id}"

    cmd = [
        "yt-dlp",
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

    return files[0] if files else None


# ======================================================
# VTT PARSER
# ======================================================

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

        ts = None
        for r in rows:
            if "-->" in r:
                ts = r
                break

        if not ts:
            continue

        timestamp = ts.split(" --> ")[0]

        idx = rows.index(ts)
        captions = rows[idx + 1:]

        parts = []

        for c in captions:
            cleaned = clean_caption_text(c)
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


# ======================================================
# PER VIDEO PROCESSOR
# ======================================================

def process_video(channel_dir, id_file, idx, video_id):

    sl_no = idx + 1

    json_files = list(channel_dir.glob(f"{sl_no}. *.json"))

    if not json_files:
        print(f"❌ JSON missing for SL {sl_no}")
        return False

    json_path = json_files[0]

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    meta = data["metadata"]

    orig_lang = meta["original_audio_language"]
    orig_code = REVERSE_LANG_MAP.get(orig_lang)

    # -----------------------------
    # remove old transcription keys
    # -----------------------------

    for k in list(data.keys()):
        if k.startswith("transcription_"):
            del data[k]

    raw = run_yt_json(video_id)

    subs = raw.get("subtitles", {})
    auto = raw.get("automatic_captions", {})

    available = set(subs.keys()) | set(auto.keys())

    tmp_dir = channel_dir / TMP_DIR_NAME

    def choose(prefix):

        if prefix in subs:
            return prefix

        for k in available:
            if k.startswith(prefix):
                return k

        return None

    anything_saved = False

    # -----------------------
    # ORIGINAL LANG
    # -----------------------

    if orig_lang == "english":

        chosen = choose("en")

        if chosen:
            vtt = download_subs(video_id, chosen, tmp_dir)
            if vtt:
                data["transcription_english"] = parse_vtt(vtt)
                anything_saved = True

    else:

        chosen_orig = choose(orig_code)

        if chosen_orig:

            vtt = download_subs(video_id, chosen_orig, tmp_dir)

            if vtt:
                data[f"transcription_{orig_lang}"] = parse_vtt(vtt)
                anything_saved = True

        # -----------------------
        # ENGLISH
        # -----------------------

        chosen_en = choose("en")

        if chosen_en:

            vtt = download_subs(video_id, chosen_en, tmp_dir)

            if vtt:
                data["transcription_english"] = parse_vtt(vtt)
                anything_saved = True

    # cleanup tmp
    for f in tmp_dir.glob("*.vtt"):
        f.unlink()

    # -----------------------
    # NOTHING FOUND
    # -----------------------

    if not anything_saved:

        print("   ⚠ No subtitles downloadable — skipping")

        return False

    # -----------------------
    # SAVE + MARK DONE
    # -----------------------

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    with open(id_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    lines[idx] = video_id + " 1 1\n"

    with open(id_file, "w", encoding="utf-8") as f:
        f.writelines(lines)

    return True


# ======================================================
# CHANNEL LOOP
# ======================================================

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

        print(f"\n▶ Processing {channel_dir.name} SL {idx+1}")

        try:

            ok = process_video(channel_dir, id_file, idx, video_id)

            if ok:
                print("   ✅ subtitles saved")

        except Exception as e:
            print("   ❌ FAILED:", e)


# ======================================================
# ENTRY
# ======================================================

if __name__ == "__main__":

    for channel_dir in BASE_DIR.iterdir():
        if channel_dir.is_dir():
            process_channel(channel_dir)
    print("\n===== STAGE-2 SUBTITLE DOWNLOAD COMPLETE =====")
