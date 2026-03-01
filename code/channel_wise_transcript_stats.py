import json
import random
from pathlib import Path

# Supports both key styles seen across runs:
# - transcript_<lang>
# - transcription_<lang>
TRANSCRIPT_PREFIXES = ("transcript_", "transcription_")

# Helper folders in data/ that are not channels
SKIP_DIRS = {"to_translate", "translated"}


def is_transcript_key(key: str) -> bool:
    return any(key.startswith(prefix) for prefix in TRANSCRIPT_PREFIXES)


def transcript_lang(key: str) -> str:
    for prefix in TRANSCRIPT_PREFIXES:
        if key.startswith(prefix):
            return key[len(prefix):].strip().lower()
    return ""


def is_non_empty(value) -> bool:
    return bool(value)


def fmt_ratio(num: int, den: int) -> str:
    pct = (num / den * 100.0) if den else 0.0
    return f"{num}/{den} ({pct:.2f}%)"


# ...existing code...

def collect_channel_stats(channel_dir: Path) -> dict:
    json_files = sorted(channel_dir.glob("*.json"))
    total = len(json_files)

    any_transcript = 0
    regional_transcript = 0
    regional_with_english = 0
    english_only = 0
    no_transcript = 0
    read_errors = 0

    # Files satisfying condition (5): no transcript or only empty transcript keys
    no_transcript_at_all_files = []

    for jf in json_files:
        try:
            data = json.loads(jf.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                read_errors += 1
                continue
        except Exception:
            read_errors += 1
            continue

        transcript_keys = [k for k in data.keys() if is_transcript_key(k)]
        non_empty_keys = [
            k for k in transcript_keys if is_non_empty(data.get(k))]

        has_any = len(non_empty_keys) > 0
        has_non_english = any(transcript_lang(
            k) != "english" for k in non_empty_keys)
        has_english = any(transcript_lang(
            k) == "english" for k in non_empty_keys)

        if has_any:
            any_transcript += 1
        else:
            no_transcript += 1
            # Add immediately when condition (5) is satisfied
            no_transcript_at_all_files.append(
                {
                    "filename": jf.name,
                    "url": data.get("metadata", {}).get("url", ""),
                }
            )

        if has_non_english:
            regional_transcript += 1
            if has_english:
                regional_with_english += 1

        if has_english and not has_non_english:
            english_only += 1

    return {
        "total": total,
        "read_errors": read_errors,
        "any_transcript": any_transcript,                    # (1)
        "regional_transcript": regional_transcript,          # (2)
        "regional_with_english": regional_with_english,      # (3) out of (2)
        "english_only": english_only,                        # (4)
        "no_transcript": no_transcript,                      # (5)
        "no_transcript_at_all_files": no_transcript_at_all_files,
    }

# ...existing code...

def main():
    base_dir = Path(__file__).resolve().parent.parent / "data"

    if not base_dir.exists():
        print(f"❌ data folder not found: {base_dir}")
        return

    channel_dirs = [
        d for d in base_dir.iterdir()
        if d.is_dir() and d.name not in SKIP_DIRS
    ]
    channel_dirs.sort(key=lambda p: p.name.lower())

    if not channel_dirs:
        print("❌ No channel folders found.")
        return

    print("\n===== CHANNEL-WISE TRANSCRIPT STATS =====\n")

    for channel_dir in channel_dirs:
        s = collect_channel_stats(channel_dir)
        total = s["total"]
        regional_total = s["regional_transcript"]

        print(f"[{channel_dir.name}]")
        print(f"Total JSON files considered: {total}")
        if s["read_errors"]:
            print(f"Read errors: {s['read_errors']}")

        print(
            "1) Non-empty transcript_<anything> present: "
            f"{fmt_ratio(s['any_transcript'], total)}"
        )
        print(
            "2) Non-empty transcript_<non-english> present: "
            f"{fmt_ratio(s['regional_transcript'], total)}"
        )
        print(
            "3) Out of (2), non-empty transcript_english present: "
            f"{fmt_ratio(s['regional_with_english'], regional_total)}"
        )
        print(
            "4) Only transcript_english (no non-english transcript): "
            f"{fmt_ratio(s['english_only'], total)}"
        )
        print(
            "5) No transcript keys or only empty transcript keys: "
            f"{fmt_ratio(s['no_transcript'], total)}"
        )

        strict_files = s["no_transcript_at_all_files"]
        print(
            f"   Strict no-transcription-at-all files (no transcript_* key): "
            f"{len(strict_files)}"
        )

        if strict_files:
            sample_n = min(5, len(strict_files))
            print(f"   Random {sample_n} sample(s) for manual testing:")
            for i, item in enumerate(random.sample(strict_files, sample_n), start=1):
                print(f"   {i}. {item['filename']} | {item.get('url', '')}")
        else:
            print("   Random samples: none (all files have transcript_* keys).")

        print("-" * 60)


if __name__ == "__main__":
    main()
