import subprocess
import json
import re

SL_NO = 4
VIDEO_ID = "oWZmPLIVy-U"


def run_yt_dlp(video_id):

    url = f"https://www.youtube.com/watch?v={video_id}"

    cmd = ["yt-dlp", "-j", url]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr)

    return json.loads(result.stdout)


def extract_clean_error(stderr_text):
    """
    Pull out the meaningful ERROR message.
    """

    # Look for explicit ERROR line
    for line in stderr_text.splitlines():
        if "ERROR:" in line:
            return line.replace("ERROR:", "").strip()

    # fallback: last non-empty line
    lines = [l.strip() for l in stderr_text.splitlines() if l.strip()]
    if lines:
        return lines[-1]

    return "Unknown error"


if __name__ == "__main__":

    print("Sl. No. | Video_id | Error")

    try:
        run_yt_dlp(VIDEO_ID)

        print(f"{SL_NO} | {VIDEO_ID} | SUCCESS (unexpected)")

    except Exception as e:

        raw_error = str(e)

        clean_error = extract_clean_error(raw_error)

        print(f"{SL_NO} | {VIDEO_ID} | {clean_error}")
