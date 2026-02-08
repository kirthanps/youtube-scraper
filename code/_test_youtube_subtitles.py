import subprocess
import json
import tempfile
from pathlib import Path

VIDEO_ID = "6JyYM4ojHGE"

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


# ---------------------------
# CORE
# ---------------------------

def run_yt_dlp_json(video_id):

    url = f"https://www.youtube.com/watch?v={video_id}"

    cmd = ["yt-dlp", "-j", url]

    res = subprocess.run(cmd, capture_output=True, text=True)

    if res.returncode != 0:
        raise RuntimeError(res.stderr)

    return json.loads(res.stdout)


def choose_best_lang(requested, available):

    # prefer exact
    if requested in available:
        return requested

    # hi-orig, en-orig, etc
    for k in available:
        if k.startswith(requested):
            return k

    return None


def fetch_subtitle_file(video_id, lang_code):

    url = f"https://www.youtube.com/watch?v={video_id}"

    with tempfile.TemporaryDirectory() as tmp:

        outtmpl = f"{tmp}/%(id)s.%(lang)s.%(ext)s"

        cmd = [
            "yt-dlp",
            "--skip-download",
            "--write-sub",
            "--write-auto-sub",
            "--sub-lang", lang_code,
            "--sub-format", "vtt",
            "-o", outtmpl,
            url
        ]

        subprocess.run(cmd, capture_output=True)

        files = list(Path(tmp).rglob("*.vtt"))

        if not files:
            return None

        # newest
        return max(files, key=lambda f: f.stat().st_mtime).read_text(encoding="utf-8")


def vtt_to_lines(vtt_text):

    lines = []

    for block in vtt_text.split("\n\n"):

        rows = block.splitlines()

        if len(rows) >= 3 and "-->" in rows[1]:

            ts = rows[1].split(" --> ")[0].strip()
            text = " ".join(rows[2:]).strip()

            if text:
                lines.append(f"[{ts}] {text}")

    return lines


# ---------------------------
# TEST
# ---------------------------

if __name__ == "__main__":

    raw = run_yt_dlp_json(VIDEO_ID)

    orig_code = raw.get("language")
    orig_lang = LANG_MAP.get(orig_code, orig_code)

    print("Original audio language:", orig_lang)

    subs = raw.get("subtitles", {})
    auto = raw.get("automatic_captions", {})

    print("\nCreator subtitles:", list(subs.keys()))
    print("Auto captions:", list(auto.keys()))

    output = {
        "metadata": {
            "title": raw.get("title"),
            "original_audio_language": orig_lang,
            "video_id": VIDEO_ID,
            "url": raw.get("webpage_url")
        }
    }

    # ---------------------
    # ORIGINAL LANG
    # ---------------------

    if orig_code:

        available = set(subs.keys()) | set(auto.keys())

        chosen = choose_best_lang(orig_code, available)

        if chosen:
            print(f"\n✔ Fetching original-language subs: {chosen}")
            txt = fetch_subtitle_file(VIDEO_ID, chosen)
            output[f"transcription_{orig_lang}"] = vtt_to_lines(
                txt) if txt else []
        else:
            print("\n⚠ No original-language subs found")

    # ---------------------
    # ENGLISH
    # ---------------------

    available = set(subs.keys()) | set(auto.keys())

    chosen_en = choose_best_lang("en", available)

    if chosen_en:
        print(f"\n✔ Fetching English subs: {chosen_en}")
        txt = fetch_subtitle_file(VIDEO_ID, chosen_en)
        output["transcription_english"] = vtt_to_lines(txt) if txt else []
    else:
        print("\n⚠ No English subs found")

    print("\n======= FINAL OUTPUT =======\n")

    print(json.dumps(output, indent=2, ensure_ascii=False))
