import subprocess

VIDEO_ID = "6JyYM4ojHGE"
LANG = "hi"   # try hindi first; later we can change to en

url = f"https://www.youtube.com/watch?v={VIDEO_ID}"

cmd = [
    "yt-dlp",
    "--skip-download",
    "--write-auto-sub",
    "--write-sub",
    "--sub-lang", LANG,
    "--sub-format", "vtt",
    url
]

print("Running command:\n", " ".join(cmd), "\n")

proc = subprocess.run(
    cmd,
    capture_output=True,
    text=True
)

print("===== STDOUT =====")
print(proc.stdout)

print("\n===== STDERR =====")
print(proc.stderr)

print("\nReturn code:", proc.returncode)
