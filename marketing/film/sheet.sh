#!/bin/sh
# Contact sheet: sheet.sh in.mp4 out.png [fps]  — tiles one frame per 1/fps seconds.
"${FFMPEG:-ffmpeg}" -y -loglevel error -i "$1" -vf "fps=${3:-1},scale=640:-1,tile=4x4:padding=6" -frames:v 1 "$2"
