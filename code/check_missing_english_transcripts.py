import json
from pathlib import Path

BASE_DIR = Path("data")

missing_english = []

print("\nScanning JSON files...\n")

for channel_dir in BASE_DIR.iterdir():

    if not channel_dir.is_dir():
        continue

    # skip helper folders
    if channel_dir.name in {"to_translate", "translated"}:
        continue

    for json_file in channel_dir.glob("*.json"):

        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

        except Exception as e:
            print(f"❌ Could not read {json_file}: {e}")
            continue

        transcription_keys = [
            k for k in data.keys()
            if k.startswith("transcription_")
            and k != "transcription_unknown"
        ]

        has_any_real = len(transcription_keys) > 0
        has_english = "transcription_english" in data

        if has_any_real and not has_english:

            missing_english.append((json_file.resolve(), transcription_keys))

            print("⚠️ Missing English:")
            print("  Path:", json_file.resolve())
            print("  Keys:", transcription_keys)
            print()

# -------------------------
# SUMMARY
# -------------------------

print("\n==============================")
print(" SUMMARY ")
print("==============================\n")

print("Total JSONs missing transcription_english:", len(missing_english))
