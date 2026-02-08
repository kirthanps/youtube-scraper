import subprocess
from pathlib import Path

VIDEO_ID = "6JyYM4ojHGE"
LANG = "hi"

OUT_DIR = Path("subs_tmp")
OUT_DIR.mkdir(exist_ok=True)

url = f"https://www.youtube.com/watch?v={VIDEO_ID}"

cmd = [
    "yt-dlp",
    "--skip-download",
    "--write-auto-sub",
    "--write-sub",
    "--sub-lang", LANG,
    "--sub-format", "vtt",
    "--paths", str(OUT_DIR),
    url
]

print("Running:\n", " ".join(cmd), "\n")

proc = subprocess.run(cmd, capture_output=True, text=True)

print("===== STDERR =====")
print(proc.stderr)

print("\nFiles created:")

files = list(OUT_DIR.glob("*.vtt"))

for f in files:
    print(" →", f.name)

    print("\nPreview:")
    print("\n".join(f.read_text(encoding="utf-8").splitlines()[:12]))

print("\nReturn code:", proc.returncode)
