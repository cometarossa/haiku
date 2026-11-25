#!/bin/sh
set -eu
cd /boot/home
mkdir -p bitmap-warm-lab
cd bitmap-warm-lab
for f in bitmap SHA256SUMS; do curl -fsS --max-time 20 http://10.0.2.2:8899/"$f" -o "$f"; done
sha256sum -c SHA256SUMS
chmod +x bitmap
marker=/boot/home/config/settings/haiku-lab-bitmap-warm
for guard in /boot/home/config/settings/haiku-lab-bitmap-warm /boot/home/config/settings/haiku-lab-bitmap-single-clear; do test ! -e "$guard" && test ! -L "$guard"; done
created=0
cleanup() { if test "$created" = 1; then rm -f "$marker"; fi; }
trap cleanup 0
trap 'exit 125' 1 2 15
if test 1 = 1; then
    (set -C; : > "$marker")
    created=1
fi
rc=0
./bitmap threads 2 64 > result.csv 2> errors.txt || rc=$?
cleanup
created=0
test ! -e "$marker" && test ! -L "$marker"
uname -a > revision.txt
printf '%s\n' "$rc" > exit.txt
for f in result.csv errors.txt revision.txt exit.txt; do curl -fsS --max-time 20 -T "$f" http://10.0.2.2:8899/"$f"; done
