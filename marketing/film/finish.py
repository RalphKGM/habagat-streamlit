"""Mux video + audio/mix.wav into final MP4s, and write subtitles, thumbnails and a GIF teaser."""
import json, os, subprocess

FF = os.environ.get("FFMPEG", "ffmpeg")
R = "renders"
TL = json.load(open("timeline.json"))


def run(*a):
    subprocess.run([FF, "-y", "-loglevel", "error", *a], check=True)


def ts(x):
    h, r = divmod(x, 3600); m, s = divmod(r, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int(round((s % 1) * 1000)):03d}"


# subtitles: one cue per voice line
with open(f"{R}/solwind_ad.srt", "w") as fh:
    for i, s in enumerate(TL["scenes"], 1):
        fh.write(f"{i}\n{ts(s['voAt'])} --> {ts(s['voAt'] + s['voDur'] + .2)}\n{' '.join(w['w'] for w in s['words'])}\n\n")

for src, dst in (("video_16x9.mp4", "solwind_ad_16x9.mp4"), ("video_9x16_cap.mp4", "solwind_ad_9x16.mp4")):
    if os.path.exists(f"{R}/{src}"):
        # JPEG frames arrive full-range; convert to standard TV-range yuv420p so every player shows the same colours.
        run("-i", f"{R}/{src}", "-i", "audio/mix.wav", "-map", "0:v", "-map", "1:a",
            "-vf", "scale=in_range=pc:out_range=tv,format=yuv420p", "-color_range", "tv", "-colorspace", "bt709",
            "-color_primaries", "bt709", "-color_trc", "bt709", "-c:v", "libx264", "-preset", "slow", "-crf", "18",
            "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", f"{R}/{dst}")
        # small copy for the share page (under 15 MB)
        os.makedirs("share", exist_ok=True)
        run("-i", f"{R}/{dst}", "-c:v", "libx264", "-preset", "slow", "-crf", "27", "-maxrate", "1500k", "-bufsize", "3000k",
            "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", f"share/{dst}")
        print("wrote", dst)

# thumbnails (the brand moment and the result) and a short silent GIF teaser of the map
S = {s["id"]: s for s in TL["scenes"]}
if os.path.exists(f"{R}/solwind_ad_16x9.mp4"):
    run("-ss", str(S["end"]["voAt"] + 2.2), "-i", f"{R}/solwind_ad_16x9.mp4", "-frames:v", "1", f"{R}/thumb_end.png")
    run("-ss", str(S["stat"]["to"] - .6), "-i", f"{R}/solwind_ad_16x9.mp4", "-frames:v", "1", f"{R}/thumb_result.png")
    run("-ss", str(S["map"]["from"] + .8), "-t", "6", "-i", f"{R}/solwind_ad_16x9.mp4", "-vf",
        "fps=15,scale=800:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=128[p];[b][p]paletteuse=dither=bayer",
        f"{R}/solwind_teaser.gif")
run("-i", f"{R}/thumb_end.png", "-vf", "scale=1280:-1", "-q:v", "3", "share/poster.jpg")
if os.path.exists(f"{R}/solwind_ad_9x16.mp4"):
    run("-ss", str(S["stat"]["to"] - .6), "-i", f"{R}/solwind_ad_9x16.mp4", "-frames:v", "1", "-vf", "scale=540:-1", "-q:v", "3", "share/poster_v.jpg")
print("done")
