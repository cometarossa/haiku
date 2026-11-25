#!/bin/sh
set -eu
cd /boot/home
mkdir -p concurrent-gui
cd concurrent-gui
for f in stream-a.mp4 stream-b.mp4 SHA256SUMS; do
 curl -fsS --connect-timeout 5 http://10.0.2.2:8899/$f -o "$f"
done
sha256sum -c SHA256SUMS
open application/x-vnd.Haiku-MediaPlayer /boot/home/concurrent-gui/stream-a.mp4
sleep 2
open application/x-vnd.Haiku-MediaPlayer /boot/home/concurrent-gui/stream-b.mp4
echo TWO_OPEN_REQUESTS_COMPLETE
