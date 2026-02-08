import json
import shutil
from pathlib import Path

BASE_DIR = Path("data")

TO_TRANSLATE_DIR = BASE_DIR / "to_translate"
TO_TRANSLATE_LIST = BASE_DIR / "to_translate.txt"

# --------------------------------------------------
# Setup output
# --------------------------------------------------

TO_TRANSLATE_DIR.mkdir(exist_ok=True)

# overwrite every run
with open(TO_TRANSLATE_LIST, "w", encoding="utf-8") as f:
    f.write("original_path | final_path\n")

count = 0

# --------------------------------------------------
# Scan channels
# --------------------------------------------------

for channel_dir in BASE_DIR.iterdir():

    if not channel_dir.is_dir():
        continue

    if channel_dir.name in {"to_translate"}:
        continue

    for json_file in channel_dir.glob("*.json"):

        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

        except Exception:
            continue

        keys = data.keys()

        non_english_transcripts = [
            k for k in keys
            if k.startswith("transcription_")
            and k != "transcription_english"
            and isinstance(data.get(k), list)
            and len(data.get(k)) > 0
        ]

        has_english = "transcription_english" in keys

        # --------------------------------------------------
        # qualifies for translation
        # --------------------------------------------------

        if non_english_transcripts and not has_english:

            dest = TO_TRANSLATE_DIR / json_file.name

            shutil.copy2(json_file, dest)

            with open(TO_TRANSLATE_LIST, "a", encoding="utf-8") as f:
                f.write(f"{json_file.resolve()} | {dest.resolve()}\n")

            count += 1

# --------------------------------------------------
# Summary
# --------------------------------------------------

print("\n===== TRANSLATION QUEUE BUILT =====")
print(f"Files copied: {count}")
print(f"List file: {TO_TRANSLATE_LIST.resolve()}")
print(f"Folder: {TO_TRANSLATE_DIR.resolve()}")
