import subprocess
from pathlib import Path
import re

# ----------------------------
# CHANNEL CONFIG
# ----------------------------

CHANNELS = {
    "masterchefnambie": "https://www.youtube.com/@Masterchefnambie",
    "delhifoodwalks": "https://www.youtube.com/@delhifoodwalks",
    "northeastindiafood": "https://www.youtube.com/c/Northeastindiafood",
    "roohi_haflongbar": "https://www.youtube.com/@roohi_haflongbar",
    "main_bhi_bharat": "https://www.youtube.com/c/MainBhiBharat"
}

BASE_DIR = Path("data")
SUMMARY_FILE = BASE_DIR / "summary_video_ids.txt"


# ----------------------------
# FETCH IDS FROM YOUTUBE
# ----------------------------

def fetch_video_ids(channel_url):
    cmd = [
        "yt-dlp",
        "--flat-playlist",
        "--print",
        "%(id)s",
        channel_url
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr)

    ids = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    return ids


# ----------------------------
# SAVE PER CHANNEL
# ----------------------------

def save_channel_ids(channel_name, ids):

    channel_dir = BASE_DIR / channel_name
    channel_dir.mkdir(parents=True, exist_ok=True)

    count = len(ids)

    outfile = channel_dir / f"video_ids_{count}.txt"

    with open(outfile, "w", encoding="utf-8") as f:
        for vid in ids:
            f.write(vid + "\n")

    return outfile


# ----------------------------
# VERIFICATION STEP
# ----------------------------

def verify_id_file(path):

    match = re.search(r"video_ids_(\d+)\.txt", path.name)

    if not match:
        return False, "Filename format invalid"

    expected_count = int(match.group(1))

    with open(path, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f.readlines() if l.strip()]

    actual_count = len(lines)

    if expected_count != actual_count:
        return False, f"COUNT MISMATCH: expected {expected_count}, got {actual_count}"

    return True, f"OK ({actual_count})"


# ----------------------------
# MAIN
# ----------------------------

if __name__ == "__main__":

    BASE_DIR.mkdir(exist_ok=True)

    summary_lines = []

    print("\n===== FETCHING VIDEO IDS =====\n")

    for name, url in CHANNELS.items():

        print(f"Processing: {name}")

        ids = fetch_video_ids(url)

        outfile = save_channel_ids(name, ids)

        print(f"  → {len(ids)} videos")
        print(f"  → saved in {outfile}")

        summary_lines.append(
            f"{name} | {len(ids)} | {outfile.as_posix()}"
        )

    # ----------------------------
    # WRITE SUMMARY
    # ----------------------------

    with open(SUMMARY_FILE, "w", encoding="utf-8") as f:
        for line in summary_lines:
            f.write(line + "\n")

    print("\n===== SUMMARY WRITTEN =====")
    print(SUMMARY_FILE)

    # ----------------------------
    # VERIFICATION PASS
    # ----------------------------

    print("\n===== VERIFICATION =====\n")

    for channel_dir in BASE_DIR.iterdir():

        if not channel_dir.is_dir():
            continue

        for txt_file in channel_dir.glob("video_ids_*.txt"):

            ok, msg = verify_id_file(txt_file)

            status = "✅" if ok else "❌"

            print(f"{status} {txt_file}: {msg}")
