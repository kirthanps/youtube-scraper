import os
import json
from pathlib import Path
from collections import defaultdict
import numpy as np

base_dir = Path("./data")

channels = [
    "delhifoodwalks",
    "main_bhi_bharat",
    "masterchefnambie",
    "northeastindiafood",
    "roohi_haflongbar"
]

# ----------------------------
# Helpers
# ----------------------------


def is_non_empty(value):
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip() != ""
    if isinstance(value, list):
        return len(value) > 0
    return False


def get_text_length(description, transcription):
    """
    Returns length of usable text
    """
    if is_non_empty(description):
        return len(description.strip())
    elif is_non_empty(transcription):
        # join list into one string
        joined = " ".join(transcription)
        return len(joined.strip())
    else:
        return 0


def get_category(description, transcription_en):
    if is_non_empty(description):
        return 0
    elif is_non_empty(transcription_en):
        return 1
    else:
        return 2

# ----------------------------
# Storage
# ----------------------------


# overall stats
overall = defaultdict(list)

# channel -> category -> lengths
channel_stats = {
    ch: defaultdict(list) for ch in channels
}

# ----------------------------
# Processing
# ----------------------------

for channel in channels:
    folder = base_dir / channel

    for file_path in folder.glob("*.json"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            description = data.get("metadata", {}).get("description", "")
            transcription_en = data.get("transcription_english", [])

            category = get_category(description, transcription_en)
            length = get_text_length(description, transcription_en)

            # store
            channel_stats[channel][category].append(length)
            overall[category].append(length)

        except Exception as e:
            print(f"Error in {file_path}: {e}")

# ----------------------------
# Function to print stats
# ----------------------------


def print_stats(name, data_dict):
    print(f"\n===== {name} =====")

    for cat in [0, 1, 2]:
        lengths = data_dict.get(cat, [])

        if len(lengths) == 0:
            print(f"Category {cat}: No data")
            continue

        print(f"\nCategory {cat}:")
        print(f"Count: {len(lengths)}")
        print(f"Min: {np.min(lengths)}")
        print(f"Max: {np.max(lengths)}")
        print(f"Avg: {np.mean(lengths):.2f}")

# ----------------------------
# Channel-wise stats
# ----------------------------


for channel in channels:
    print_stats(f"CHANNEL: {channel}", channel_stats[channel])

# ----------------------------
# Overall stats
# ----------------------------

print_stats("OVERALL", overall)


'''
Results:
===== CHANNEL: delhifoodwalks =====

Category 0:
Count: 661
Min: 20
Max: 4996
Avg: 2876.88

Category 1:
Count: 73
Min: 73
Max: 130642
Avg: 23642.21

Category 2:
Count: 4
Min: 0
Max: 0
Avg: 0.00

===== CHANNEL: main_bhi_bharat =====

Category 0:
Count: 859
Min: 12
Max: 3555
Avg: 624.09

Category 1:
Count: 252
Min: 22
Max: 140743
Avg: 5801.36

Category 2:
Count: 44
Min: 0
Max: 0
Avg: 0.00

===== CHANNEL: masterchefnambie =====

Category 0:
Count: 191
Min: 68
Max: 4751
Avg: 732.85

Category 1:
Count: 44
Min: 155
Max: 3967
Avg: 2474.95

Category 2:
Count: 4
Min: 0
Max: 0
Avg: 0.00

===== CHANNEL: northeastindiafood =====

Category 0:
Count: 125
Min: 39
Max: 558
Avg: 162.21

Category 1:
Count: 1
Min: 45
Max: 45
Avg: 45.00

Category 2:
Count: 3
Min: 0
Max: 0
Avg: 0.00

===== CHANNEL: roohi_haflongbar =====

Category 0:
Count: 5
Min: 358
Max: 1392
Avg: 808.40

Category 1:
Count: 73
Min: 297
Max: 21004
Avg: 3885.42

Category 2:
Count: 2
Min: 0
Max: 0
Avg: 0.00

===== OVERALL =====

Category 0:
Count: 1841
Min: 12
Max: 4996
Avg: 1413.36

Category 1:
Count: 443
Min: 22
Max: 140743
Avg: 8082.17

Category 2:
Count: 57
Min: 0
Max: 0
Avg: 0.00
'''
