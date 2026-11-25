#!/bin/sh
set -eu
cd /boot/home/v17-catchup-16-long-ram
for ext in stdout stderr latency exit; do
 f=01-n16-on.$ext
 test -f "$f"
 curl -fsS -T "$f" "http://10.0.2.2:8901/$f"
done
for m in haiku-lab-media-stats haiku-lab-media-overlay-preflight haiku-lab-media-catchup haiku-lab-media-catchup-adaptive; do
 test ! -e "/boot/home/config/settings/$m"
done
printf '0\n' > recovery-complete.txt
curl -fsS -T recovery-complete.txt http://10.0.2.2:8901/recovery-complete.txt
