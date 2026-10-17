#!/bin/sh
# Combine the silent render with the generated soundtrack into the final post-ready MP4.
set -e
cd "$(dirname "$0")"
ffmpeg -y -loglevel error -i startale-usdc-vaults-silent.mp4 -i soundtrack.wav \
  -map 0:v -map 1:a -c:v copy -c:a aac -b:a 256k -ar 48000 -shortest -movflags +faststart \
  startale-usdc-vaults.mp4
echo "wrote startale-usdc-vaults.mp4"
