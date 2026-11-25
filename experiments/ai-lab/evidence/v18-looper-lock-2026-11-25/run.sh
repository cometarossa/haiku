#!/bin/sh
set -eu
cd /boot/home
mkdir v18-looper-lock-probe
cd v18-looper-lock-probe
for f in looper-lock-probe SHA256SUMS; do curl -fsS "http://10.0.2.2:8901/$f" -o "$f"; done
sha256sum -c SHA256SUMS
chmod +x looper-lock-probe
uname -a > revision.txt
rc=0
./looper-lock-probe > probe.stdout 2> probe.stderr || rc=$?
printf '%s\n' "$rc" > probe.exit
for f in revision.txt probe.stdout probe.stderr probe.exit; do curl -fsS -T "$f" "http://10.0.2.2:8901/$f"; done
