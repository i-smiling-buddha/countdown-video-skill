#!/usr/bin/env bash
# items.json -> countdown MP4 (+ QA sheet + YouTube chapters)
# Usage: make_countdown.sh items.json out.mp4 [chunks=nproc] [-- extra args for countdown_audio.py]
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
SRC="$(realpath "$1")"; OUT="$2"; CH="${3:-$(nproc)}"; shift $(( $# >= 3 ? 3 : $# )); [ "${1:-}" = "--" ] && shift
WORK="$(dirname "$SRC")/_work"; mkdir -p "$WORK"
python3 "$HERE/build_countdown.py" "$SRC" "$WORK"
N=$(python3 -c "import json;t=json.load(open('$WORK/timeline.json'));print(int(round((t[-1]['start']+t[-1]['dur'])*30)))")
STEP=$(( (N + CH - 1) / CH )); : > "$WORK/list.txt"
for ((i=0; i<CH; i++)); do
  F0=$((i*STEP)); F1=$(( F0+STEP < N ? F0+STEP : N ))
  python3 "$HERE/render.py" "$WORK/build.html" "$WORK/chunk_$i.mp4" --from $F0 --to $F1 &
  echo "file 'chunk_$i.mp4'" >> "$WORK/list.txt"
done; wait
ffmpeg -y -loglevel error -f concat -safe 0 -i "$WORK/list.txt" -c copy "$WORK/video.mp4"
VID="$WORK/video.mp4"
if grep -q '"kind": "clip"' "$WORK/timeline.json"; then python3 "$HERE/compose_clips.py" "$WORK" && VID="$WORK/video_clips.mp4"; fi
python3 "$HERE/countdown_audio.py" "$WORK" "$WORK/mix.wav" "$@"
ffmpeg -y -loglevel error -i "$VID" -i "$WORK/mix.wav" -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest "$OUT"
ffmpeg -y -loglevel error -i "$OUT" -vf "fps=1/4,scale=320:-1,tile=6x6" -frames:v 1 "${OUT%.mp4}_sheet.png"
cp "$WORK/chapters.txt" "${OUT%.mp4}_chapters.txt"
echo "Done: $OUT"; echo "QA sheet: ${OUT%.mp4}_sheet.png"; echo "YouTube chapters (paste in description):"; cat "$WORK/chapters.txt"
