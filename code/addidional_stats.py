import json
import re
from collections import Counter
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent / "data"
SKIP_DIRS = {
    "to_translate",
    "translated",
    "to_translate_old",
    "translated_old",
    "splits_for_video_type",
}
EXPECTED_VIDEO_TYPES = {"food", "news", "other", "unpredictable"}


def pct(part, whole):
    if whole == 0:
        return "0.00%"
    return f"{(part / whole) * 100:.2f}%"


def parse_expected_total(id_file_name):
    match = re.search(r"video_ids_(\d+)\.txt", id_file_name)
    if not match:
        return None
    return int(match.group(1))


def non_empty(value):
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return len(value) > 0
    return True


def parse_id_file(id_file):
    lines = id_file.read_text(encoding="utf-8").splitlines()

    stage2 = 0
    stage1 = 0
    errored = 0
    raw = 0
    malformed = 0

    for line in lines:
        value = line.strip()
        if not value:
            continue

        if value.endswith(" 1 1"):
            stage2 += 1
        elif value.endswith(" 1"):
            stage1 += 1
        elif value.endswith(" e"):
            errored += 1
        elif " " in value:
            malformed += 1
        else:
            raw += 1

    return {
        "line_count": len([x for x in lines if x.strip()]),
        "stage1": stage1,
        "stage2": stage2,
        "errored": errored,
        "raw": raw,
        "malformed": malformed,
    }


def collect_json_metrics(channel_dir):
    json_files = sorted(channel_dir.glob("*.json"))

    metrics = {
        "json_total": len(json_files),
        "read_errors": 0,
        "with_any_transcription": 0,
        "with_non_empty_english": 0,
        "with_non_english": 0,
        "with_video_type": 0,
        "missing_video_type": 0,
        "unexpected_video_type": 0,
        "video_type_counts": Counter(),
    }

    for jf in json_files:
        try:
            data = json.loads(jf.read_text(encoding="utf-8"))
        except Exception:
            metrics["read_errors"] += 1
            continue

        transcription_keys = [
            k for k in data.keys() if k.startswith("transcription_")]

        non_empty_transcription_keys = [
            k for k in transcription_keys if non_empty(data.get(k))
        ]

        if non_empty_transcription_keys:
            metrics["with_any_transcription"] += 1

        if "transcription_english" in data and non_empty(data.get("transcription_english")):
            metrics["with_non_empty_english"] += 1

        has_non_english = any(
            k != "transcription_english" for k in non_empty_transcription_keys)
        if has_non_english:
            metrics["with_non_english"] += 1

        if "video_type" not in data:
            metrics["missing_video_type"] += 1
            continue

        value = str(data.get("video_type") or "").strip().lower()
        if value in EXPECTED_VIDEO_TYPES:
            metrics["with_video_type"] += 1
            metrics["video_type_counts"][value] += 1
        else:
            metrics["unexpected_video_type"] += 1

    return metrics


def print_channel_report(channel_name, id_metrics, json_metrics, expected_total):
    lines_in_id = id_metrics["line_count"]
    processed_stage1_or_more = id_metrics["stage1"] + \
        id_metrics["stage2"] + id_metrics["errored"]

    print(f"\n===== {channel_name} =====")
    print(f"Expected IDs from filename: {expected_total}")
    print(f"Actual non-empty ID lines: {lines_in_id}")
    print(
        "ID file health: "
        f"raw={id_metrics['raw']}, stage1={id_metrics['stage1']}, stage2={id_metrics['stage2']}, "
        f"errored={id_metrics['errored']}, malformed={id_metrics['malformed']}"
    )

    if expected_total is not None:
        print(
            "ID coverage vs expected: "
            f"{processed_stage1_or_more}/{expected_total} ({pct(processed_stage1_or_more, expected_total)})"
        )

    print(
        "Transcription completion (stage2 marker): "
        f"{id_metrics['stage2']}/{lines_in_id} ({pct(id_metrics['stage2'], lines_in_id)})"
    )
    print(
        "Metadata completion (stage1 or stage2): "
        f"{id_metrics['stage1'] + id_metrics['stage2']}/{lines_in_id} "
        f"({pct(id_metrics['stage1'] + id_metrics['stage2'], lines_in_id)})"
    )

    print(f"JSON files found: {json_metrics['json_total']}")
    print(
        "JSON with any non-empty transcription_: "
        f"{json_metrics['with_any_transcription']}/{json_metrics['json_total']} "
        f"({pct(json_metrics['with_any_transcription'], json_metrics['json_total'])})"
    )
    print(
        "JSON with non-empty transcription_english: "
        f"{json_metrics['with_non_empty_english']}/{json_metrics['json_total']} "
        f"({pct(json_metrics['with_non_empty_english'], json_metrics['json_total'])})"
    )
    print(
        "JSON with any non-English transcription_: "
        f"{json_metrics['with_non_english']}/{json_metrics['json_total']} "
        f"({pct(json_metrics['with_non_english'], json_metrics['json_total'])})"
    )

    print(
        "Video type coverage: "
        f"{json_metrics['with_video_type']}/{json_metrics['json_total']} "
        f"({pct(json_metrics['with_video_type'], json_metrics['json_total'])})"
    )

    if json_metrics["unexpected_video_type"]:
        print(
            f"Unexpected video_type values: {json_metrics['unexpected_video_type']}")
    if json_metrics["read_errors"]:
        print(f"Unreadable JSON files: {json_metrics['read_errors']}")

    if json_metrics["video_type_counts"]:
        print("video_type distribution:")
        for label in ["food", "news", "other", "unpredictable"]:
            count = json_metrics["video_type_counts"].get(label, 0)
            print(
                f"  - {label}: {count} "
                f"({pct(count, json_metrics['with_video_type'])} of typed)"
            )


def main():
    if not BASE_DIR.exists():
        print(f"data folder not found: {BASE_DIR}")
        return

    channel_dirs = [
        d for d in BASE_DIR.iterdir()
        if d.is_dir() and d.name not in SKIP_DIRS
    ]
    channel_dirs.sort(key=lambda p: p.name.lower())

    if not channel_dirs:
        print("No channel folders found under data/")
        return

    overall = {
        "expected_total": 0,
        "id_lines": 0,
        "raw": 0,
        "stage1": 0,
        "stage2": 0,
        "errored": 0,
        "malformed": 0,
        "json_total": 0,
        "with_any_transcription": 0,
        "with_non_empty_english": 0,
        "with_non_english": 0,
        "with_video_type": 0,
        "missing_video_type": 0,
        "unexpected_video_type": 0,
        "read_errors": 0,
        "video_type_counts": Counter(),
    }

    print("===== ADDIDIONAL PIPELINE STATS =====")

    for channel_dir in channel_dirs:
        id_files = sorted(channel_dir.glob("video_ids_*.txt"))
        if not id_files:
            print(f"\n===== {channel_dir.name} =====")
            print("No video_ids_*.txt file found. Skipping marker-based metrics.")
            continue

        id_file = id_files[0]
        expected_total = parse_expected_total(id_file.name)
        id_metrics = parse_id_file(id_file)
        json_metrics = collect_json_metrics(channel_dir)

        print_channel_report(channel_dir.name, id_metrics,
                             json_metrics, expected_total)

        overall["expected_total"] += expected_total or 0
        overall["id_lines"] += id_metrics["line_count"]
        overall["raw"] += id_metrics["raw"]
        overall["stage1"] += id_metrics["stage1"]
        overall["stage2"] += id_metrics["stage2"]
        overall["errored"] += id_metrics["errored"]
        overall["malformed"] += id_metrics["malformed"]
        overall["json_total"] += json_metrics["json_total"]
        overall["with_any_transcription"] += json_metrics["with_any_transcription"]
        overall["with_non_empty_english"] += json_metrics["with_non_empty_english"]
        overall["with_non_english"] += json_metrics["with_non_english"]
        overall["with_video_type"] += json_metrics["with_video_type"]
        overall["missing_video_type"] += json_metrics["missing_video_type"]
        overall["unexpected_video_type"] += json_metrics["unexpected_video_type"]
        overall["read_errors"] += json_metrics["read_errors"]
        overall["video_type_counts"].update(json_metrics["video_type_counts"])

    processed_stage1_or_more = overall["stage1"] + \
        overall["stage2"] + overall["errored"]

    print("\n===== OVERALL =====")
    print(f"Expected IDs from filenames: {overall['expected_total']}")
    print(f"Actual non-empty ID lines: {overall['id_lines']}")
    print(
        "ID markers totals: "
        f"raw={overall['raw']}, stage1={overall['stage1']}, stage2={overall['stage2']}, "
        f"errored={overall['errored']}, malformed={overall['malformed']}"
    )
    print(
        "ID coverage vs expected: "
        f"{processed_stage1_or_more}/{overall['expected_total']} "
        f"({pct(processed_stage1_or_more, overall['expected_total'])})"
    )
    print(
        "Transcription completion (stage2 marker): "
        f"{overall['stage2']}/{overall['id_lines']} ({pct(overall['stage2'], overall['id_lines'])})"
    )
    print(f"Total JSON files: {overall['json_total']}")
    print(
        "JSON with any non-empty transcription_: "
        f"{overall['with_any_transcription']}/{overall['json_total']} "
        f"({pct(overall['with_any_transcription'], overall['json_total'])})"
    )
    print(
        "JSON with non-empty transcription_english: "
        f"{overall['with_non_empty_english']}/{overall['json_total']} "
        f"({pct(overall['with_non_empty_english'], overall['json_total'])})"
    )
    print(
        "JSON with any non-English transcription_: "
        f"{overall['with_non_english']}/{overall['json_total']} "
        f"({pct(overall['with_non_english'], overall['json_total'])})"
    )
    print(
        "Video type coverage: "
        f"{overall['with_video_type']}/{overall['json_total']} "
        f"({pct(overall['with_video_type'], overall['json_total'])})"
    )

    if overall["unexpected_video_type"]:
        print(
            f"Unexpected video_type values: {overall['unexpected_video_type']}")
    if overall["read_errors"]:
        print(f"Unreadable JSON files: {overall['read_errors']}")

    if overall["video_type_counts"]:
        print("video_type distribution:")
        for label in ["food", "news", "other", "unpredictable"]:
            count = overall["video_type_counts"].get(label, 0)
            print(
                f"  - {label}: {count} ({pct(count, overall['with_video_type'])} of typed)")


if __name__ == "__main__":
    main()
