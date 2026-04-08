import json
from pathlib import Path

# Helper folders in data/ that are not channel folders.
SKIP_DIRS = {"to_translate", "to_translate_old",
             "translated", "translated_old"}


def has_non_empty_description(data: dict) -> bool:
    metadata = data.get("metadata", {}) if isinstance(data, dict) else {}
    description = metadata.get(
        "description", "") if isinstance(metadata, dict) else ""
    return isinstance(description, str) and bool(description.strip())


def has_non_empty_transcription_english(data: dict) -> bool:
    if not isinstance(data, dict):
        return False

    if "transcription_english" not in data:
        return False

    value = data.get("transcription_english")

    if isinstance(value, str):
        return bool(value.strip())

    if isinstance(value, (list, dict, tuple, set)):
        return len(value) > 0

    return value is not None


def collect_stats_for_dir(channel_dir: Path) -> dict:
    json_files = sorted(channel_dir.rglob("*.json"))

    with_description = 0
    without_desc_with_non_empty_english = 0
    without_both = 0
    read_errors = 0

    for json_file in json_files:
        try:
            payload = json.loads(json_file.read_text(encoding="utf-8"))
        except Exception:
            read_errors += 1
            continue

        has_description = has_non_empty_description(payload)
        has_english = has_non_empty_transcription_english(payload)

        if has_description:
            with_description += 1
        elif has_english:
            without_desc_with_non_empty_english += 1
        else:
            without_both += 1

    return {
        "total_json": len(json_files),
        "with_description": with_description,
        "without_desc_with_non_empty_english": without_desc_with_non_empty_english,
        "without_both": without_both,
        "read_errors": read_errors,
    }


def main() -> None:
    base_dir = Path(__file__).resolve().parent.parent / "data"

    if not base_dir.exists():
        print(f"data folder not found: {base_dir}")
        return

    channel_dirs = [
        path
        for path in base_dir.iterdir()
        if path.is_dir() and path.name not in SKIP_DIRS
    ]
    channel_dirs.sort(key=lambda p: p.name.lower())

    if not channel_dirs:
        print("No channel folders found under data/.")
        return

    total_stats = {
        "total_json": 0,
        "with_description": 0,
        "without_desc_with_non_empty_english": 0,
        "without_both": 0,
        "read_errors": 0,
    }

    print("\n===== DESCRIPTION / TRANSCRIPTION_ENGLISH STATS (PER CHANNEL) =====\n")

    for channel_dir in channel_dirs:
        stats = collect_stats_for_dir(channel_dir)

        print(f"[{channel_dir.name}]")
        print(f"Total JSON files: {stats['total_json']}")
        print(f"1) With description: {stats['with_description']}")
        print(
            "2) Without description but with non-empty transcription_english: "
            f"{stats['without_desc_with_non_empty_english']}"
        )
        print(f"3) Without both: {stats['without_both']}")
        if stats["read_errors"]:
            print(f"Read errors: {stats['read_errors']}")
        print("-" * 60)

        for key in total_stats:
            total_stats[key] += stats[key]

    print("\n===== TOTAL ACROSS ALL CHANNELS =====")
    print(f"Total JSON files: {total_stats['total_json']}")
    print(f"1) With description: {total_stats['with_description']}")
    print(
        "2) Without description but with non-empty transcription_english: "
        f"{total_stats['without_desc_with_non_empty_english']}"
    )
    print(f"3) Without both: {total_stats['without_both']}")
    if total_stats["read_errors"]:
        print(f"Read errors: {total_stats['read_errors']}")


if __name__ == "__main__":
    main()
