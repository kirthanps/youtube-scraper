import json
from pathlib import Path
import re
import sys

BASE_DIR = Path("data")


# -----------------------------
# HELPERS
# -----------------------------

def parse_expected_total(filename):
    m = re.search(r"video_ids_(\d+)\.txt", filename)
    return int(m.group(1)) if m else None


def load_error_file(error_file):

    with open(error_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    header = lines[0].strip()
    entries = lines[1:]

    ids = set()

    for line in entries:
        parts = line.split("|")
        if len(parts) >= 3:
            ids.add(parts[1].strip())

    return header, entries, ids


def find_json_by_slno(channel_dir, slno):

    for f in channel_dir.glob(f"{slno}. *.json"):
        return f

    return None


def validate_json_file(path, expected_video_id):

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return False, f"Invalid JSON: {e}"

    if "metadata" not in data:
        return False, "Missing metadata"

    meta = data["metadata"]

    required_meta = [
        "title",
        "channel_name",
        "publish_date",
        "view_count",
        "like_count",
        "duration",
        "original_audio_language",
        "video_id",
        "url",
        "description",
        "ingredients_detected"
    ]

    for key in required_meta:
        if key not in meta:
            return False, f"Missing metadata field: {key}"

    if meta["video_id"] != expected_video_id:
        return False, "Video ID mismatch in JSON"

    transcription_keys = [k for k in data if k.startswith("transcription_")]

    if len(transcription_keys) != 1:
        return False, f"Expected 1 transcription key, found {len(transcription_keys)}"

    if not isinstance(data[transcription_keys[0]], list):
        return False, "Transcription value is not a list"

    return True, "OK"


# -----------------------------
# MAIN VERIFIER
# -----------------------------

def verify_channel(channel_dir):

    print(f"\n===== VERIFYING {channel_dir.name} =====")

    id_files = list(channel_dir.glob("video_ids_*.txt"))

    if not id_files:
        print("❌ Missing video_ids file")
        return

    id_file = id_files[0]

    expected_total = parse_expected_total(id_file.name)

    with open(id_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    success = []
    errors = []

    for idx, raw in enumerate(lines):
        line = raw.strip()

        if not line:
            continue

        slno = idx + 1

        if line.endswith(" 1"):
            success.append((slno, line[:-2]))
        elif line.endswith(" e"):
            errors.append((slno, line[:-2]))

    print(f"Expected total : {expected_total}")
    print(f"Processed OK   : {len(success)}")
    print(f"Errored        : {len(errors)}")

    # ---- Step 1 ----
    if expected_total is not None:
        if len(success) + len(errors) != expected_total:
            print("❌ COUNT MISMATCH vs filename")
        else:
            print("✅ ID coverage matches filename")

    # ---- Step 2 ----
    error_file = channel_dir / f"errors_{len(errors)}.txt"

    if len(errors) > 0:

        if not error_file.exists():
            print(f"❌ Missing {error_file.name}")
            return

        print(f"✅ Found {error_file.name}")

        # ---- Step 3 ----
        header, entries, logged_ids = load_error_file(error_file)

        if len(entries) != len(errors):
            print("❌ Error file line count mismatch")
        else:
            print("✅ Error file line count correct")

        # ---- Step 4 ----
        missing = []

        for slno, vid in errors:
            if vid not in logged_ids:
                missing.append(vid)

        if missing:
            print("❌ IDs marked 'e' but not in error log:")
            for m in missing:
                print("   ", m)
        else:
            print("✅ All errored IDs present in error log")

    else:
        print("ℹ️ No errors for this channel")

    # ---- Step 5 ----
    print("\nChecking JSON files...")

    for slno, vid in success:

        json_path = find_json_by_slno(channel_dir, slno)

        if not json_path:
            print(f"❌ Missing JSON for SL {slno}")
            continue

        ok, msg = validate_json_file(json_path, vid)

        if not ok:
            print(f"❌ {json_path.name}: {msg}")
        else:
            print(f"✅ {json_path.name}")


# -----------------------------
# ENTRYPOINT
# -----------------------------

if __name__ == "__main__":

    if not BASE_DIR.exists():
        print("❌ data/ folder not found")
        sys.exit(1)

    for channel_dir in BASE_DIR.iterdir():

        if channel_dir.is_dir():
            verify_channel(channel_dir)

    print("\n===== VERIFICATION COMPLETE =====")
