import shutil
from pathlib import Path

BASE_DIR = Path("data")

LIST_FILE = BASE_DIR / "to_translate.txt"
TRANSLATED_DIR = BASE_DIR / "translated"

# --------------------------------------------------
# Safety checks
# --------------------------------------------------

if not LIST_FILE.exists():
    raise RuntimeError(f"Missing {LIST_FILE}")

if not TRANSLATED_DIR.exists():
    raise RuntimeError(f"Missing {TRANSLATED_DIR}")

# --------------------------------------------------
# Main restore loop
# --------------------------------------------------

restored = 0
missing = 0

with open(LIST_FILE, "r", encoding="utf-8") as f:

    lines = f.readlines()

for i, raw in enumerate(lines):

    # skip header
    if i == 0:
        continue

    raw = raw.strip()

    if not raw:
        continue

    try:
        original_path, final_path = raw.split(" | ")

    except ValueError:
        print(f"⚠ Bad line format: {raw}")
        continue

    original_path = Path(original_path)
    final_path = Path(final_path)

    filename = final_path.name

    translated_file = TRANSLATED_DIR / filename

    if not translated_file.exists():

        print(f"❌ Missing translated file: {translated_file}")
        missing += 1
        continue

    if not original_path.parent.exists():
        print(f"❌ Original folder missing: {original_path.parent}")
        missing += 1
        continue

    # overwrite original
    shutil.move(str(translated_file), str(original_path))

    print(f"✅ Restored → {original_path}")

    restored += 1

# --------------------------------------------------
# Summary
# --------------------------------------------------

print("\n===== RESTORE COMPLETE =====")
print(f"Files restored: {restored}")
print(f"Missing files: {missing}")
