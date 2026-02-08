# this is a test script to fetch metadata for a single video and build the template
import subprocess
import json
from datetime import timedelta

VIDEO_ID = "-SkduwWN12o"


def run_yt_dlp(video_id):

    url = f"https://www.youtube.com/watch?v={video_id}"

    cmd = [
        "yt-dlp",
        "-j",           # dump full JSON
        url
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr)

    return json.loads(result.stdout)


def seconds_to_hms(seconds):
    if not seconds:
        return None
    return str(timedelta(seconds=int(seconds)))


def build_template(raw):

    metadata = {
        "title": raw.get("title"),
        "channel_name": raw.get("channel"),
        "publish_date": raw.get("upload_date"),
        "view_count": raw.get("view_count"),
        "like_count": raw.get("like_count"),
        "duration": seconds_to_hms(raw.get("duration")),
        "original_audio_language": raw.get("language"),
        "video_id": raw.get("id"),
        "url": raw.get("webpage_url"),
        "description": raw.get("description"),

        # PLACEHOLDERS
        "ingredients_detected": []
    }

    output = {
        "metadata": metadata,

        # PLACEHOLDER – will fill later
        "transcription_original_audio_language": []
    }

    return output


if __name__ == "__main__":

    print(f"\nFetching metadata for video: {VIDEO_ID}\n")

    raw_data = run_yt_dlp(VIDEO_ID)

    final_json = build_template(raw_data)

    print(json.dumps(final_json, indent=2, ensure_ascii=False))
