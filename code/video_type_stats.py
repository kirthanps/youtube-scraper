import json
from collections import Counter
from pathlib import Path


EXPECTED_VIDEO_TYPES = ["food", "news", "other", "unpredictable"]
SKIP_DIRS = {
    "splits_for_video_type",
    "to_translate",
    "to_translate_old",
    "translated",
    "translated_old",
}


def pct(part: int, whole: int) -> str:
    if whole == 0:
        return "0.00%"
    return f"{(part / whole) * 100:.2f}%"


def normalize_video_type(value):
    if value is None:
        return None
    if isinstance(value, str):
        cleaned = value.strip().lower()
        return cleaned or None
    return str(value).strip().lower() or None


def collect_channel_stats(channel_dir: Path) -> dict:
    json_files = sorted(channel_dir.glob("*.json"))

    stats = {
        "total_json": len(json_files),
        "with_video_type": 0,
        "missing_video_type": 0,
        "uncovered": 0,
        "read_errors": 0,
        "category_counts": Counter(),
        "unexpected_values": Counter(),
    }

    for json_file in json_files:
        try:
            payload = json.loads(json_file.read_text(encoding="utf-8"))
        except Exception:
            stats["read_errors"] += 1
            stats["uncovered"] += 1
            continue

        if not isinstance(payload, dict):
            stats["uncovered"] += 1
            continue

        if "video_type" not in payload:
            stats["missing_video_type"] += 1
            stats["uncovered"] += 1
            continue

        stats["with_video_type"] += 1
        video_type = normalize_video_type(payload.get("video_type"))

        if video_type in EXPECTED_VIDEO_TYPES:
            stats["category_counts"][video_type] += 1
        else:
            stats["unexpected_values"][video_type or "<empty>"] += 1
            stats["uncovered"] += 1

    return stats


def print_channel_stats(channel_name: str, stats: dict) -> None:
    total_json = stats["total_json"]
    with_video_type = stats["with_video_type"]

    print(f"\n[{channel_name}]")
    print(f"Total JSON files: {total_json}")
    print(
        f"Files with video_type: {with_video_type} "
        f"({pct(with_video_type, total_json)})"
    )
    print(
        f"Missing video_type: {stats['missing_video_type']} "
        f"({pct(stats['missing_video_type'], total_json)})"
    )
    print(
        f"Uncovered files: {stats['uncovered']} "
        f"({pct(stats['uncovered'], total_json)})"
    )

    print("Category breakdown among files with video_type:")
    for category in EXPECTED_VIDEO_TYPES:
        count = stats["category_counts"].get(category, 0)
        print(
            f"  - {category}: {count} "
            f"({pct(count, with_video_type)} of video_type files, "
            f"{pct(count, total_json)} of all files)"
        )

    if stats["unexpected_values"]:
        print("  - unexpected values:")
        for value, count in stats["unexpected_values"].most_common():
            print(f"    * {value}: {count}")


def print_overall_stats(overall: dict) -> None:
    total_json = overall["total_json"]
    with_video_type = overall["with_video_type"]

    print("\n===== OVERALL =====")
    print(f"Total JSON files: {total_json}")
    print(
        f"Files with video_type: {with_video_type} "
        f"({pct(with_video_type, total_json)})"
    )
    print(
        f"Missing video_type: {overall['missing_video_type']} "
        f"({pct(overall['missing_video_type'], total_json)})"
    )
    print(
        f"Uncovered files: {overall['uncovered']} "
        f"({pct(overall['uncovered'], total_json)})"
    )
    print("Category breakdown among files with video_type:")
    for category in EXPECTED_VIDEO_TYPES:
        count = overall["category_counts"].get(category, 0)
        print(
            f"  - {category}: {count} "
            f"({pct(count, with_video_type)} of video_type files, "
            f"{pct(count, total_json)} of all files)"
        )

    if overall["unexpected_values"]:
        print("  - unexpected values:")
        for value, count in overall["unexpected_values"].most_common():
            print(f"    * {value}: {count}")


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
    channel_dirs.sort(key=lambda path: path.name.lower())

    if not channel_dirs:
        print("No channel folders found under data/.")
        return

    overall = {
        "total_json": 0,
        "with_video_type": 0,
        "missing_video_type": 0,
        "uncovered": 0,
        "read_errors": 0,
        "category_counts": Counter(),
        "unexpected_values": Counter(),
    }

    print("===== VIDEO TYPE STATS (PER CHANNEL) =====")

    for channel_dir in channel_dirs:
        stats = collect_channel_stats(channel_dir)
        print_channel_stats(channel_dir.name, stats)

        overall["total_json"] += stats["total_json"]
        overall["with_video_type"] += stats["with_video_type"]
        overall["missing_video_type"] += stats["missing_video_type"]
        overall["uncovered"] += stats["uncovered"]
        overall["read_errors"] += stats["read_errors"]
        overall["category_counts"].update(stats["category_counts"])
        overall["unexpected_values"].update(stats["unexpected_values"])

    print_overall_stats(overall)

    if overall["read_errors"]:
        print(f"Read errors: {overall['read_errors']}")


if __name__ == "__main__":
    main()


'''
Results:
===== VIDEO TYPE STATS (PER CHANNEL) =====

[delhifoodwalks]
Total JSON files: 738
Files with video_type: 738 (100.00%)
Missing video_type: 0 (0.00%)
Uncovered files: 0 (0.00%)
Category breakdown among files with video_type:
  - food: 657 (89.02% of video_type files, 89.02% of all files)
  - news: 17 (2.30% of video_type files, 2.30% of all files)
  - other: 37 (5.01% of video_type files, 5.01% of all files)
  - unpredictable: 27 (3.66% of video_type files, 3.66% of all files)

[main_bhi_bharat]
Total JSON files: 1155
Files with video_type: 1155 (100.00%)
Missing video_type: 0 (0.00%)
Uncovered files: 0 (0.00%)
Category breakdown among files with video_type:
  - food: 244 (21.13% of video_type files, 21.13% of all files)
  - news: 583 (50.48% of video_type files, 50.48% of all files)
  - other: 290 (25.11% of video_type files, 25.11% of all files)
  - unpredictable: 38 (3.29% of video_type files, 3.29% of all files)

[masterchefnambie]
Total JSON files: 239
Files with video_type: 239 (100.00%)
Missing video_type: 0 (0.00%)
Uncovered files: 0 (0.00%)
Category breakdown among files with video_type:
  - food: 204 (85.36% of video_type files, 85.36% of all files)
  - news: 6 (2.51% of video_type files, 2.51% of all files)
  - other: 21 (8.79% of video_type files, 8.79% of all files)
  - unpredictable: 8 (3.35% of video_type files, 3.35% of all files)

[northeastindiafood]
Total JSON files: 129
Files with video_type: 129 (100.00%)
Missing video_type: 0 (0.00%)
Uncovered files: 0 (0.00%)
Category breakdown among files with video_type:
  - food: 121 (93.80% of video_type files, 93.80% of all files)
  - news: 1 (0.78% of video_type files, 0.78% of all files)
  - other: 2 (1.55% of video_type files, 1.55% of all files)
  - unpredictable: 5 (3.88% of video_type files, 3.88% of all files)

[roohi_haflongbar]
Total JSON files: 80
Files with video_type: 80 (100.00%)
Missing video_type: 0 (0.00%)
Uncovered files: 0 (0.00%)
Category breakdown among files with video_type:
  - food: 79 (98.75% of video_type files, 98.75% of all files)
  - news: 0 (0.00% of video_type files, 0.00% of all files)
  - other: 1 (1.25% of video_type files, 1.25% of all files)
  - unpredictable: 0 (0.00% of video_type files, 0.00% of all files)

===== OVERALL =====
Total JSON files: 2341
Files with video_type: 2341 (100.00%)
Missing video_type: 0 (0.00%)
Uncovered files: 0 (0.00%)
Category breakdown among files with video_type:
  - food: 1305 (55.75% of video_type files, 55.75% of all files)
  - news: 607 (25.93% of video_type files, 25.93% of all files)
  - other: 351 (14.99% of video_type files, 14.99% of all files)
  - unpredictable: 78 (3.33% of video_type files, 3.33% of all files)
'''
