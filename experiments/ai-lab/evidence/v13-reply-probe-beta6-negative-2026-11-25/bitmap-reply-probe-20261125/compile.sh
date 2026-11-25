#!/bin/sh
set -eu
cd /boot/home
mkdir -p bitmap-reply-probe-lab
cd bitmap-reply-probe-lab
curl -fsS http://10.0.2.2:8901/probe.cpp -o probe.cpp
rc=0
g++ -std=c++11 -O2 -Wall -Wextra -I/boot/system/develop/headers/private/app -o probe probe.cpp -lbe > compile.log 2>&1 || rc=$?
printf '%s\n' "$rc" > compile.exit
uname -a > revision.txt
for f in compile.log revision.txt compile.exit; do curl -fsS -T "$f" http://10.0.2.2:8901/"$f"; done
test "$rc" = 0
sha256sum probe > SHA256SUMS
for f in probe SHA256SUMS; do curl -fsS -T "$f" http://10.0.2.2:8901/"$f"; done
for f in haiku-lab-bitmap-warm haiku-lab-bitmap-single-clear haiku-lab-bitmap-quiet; do test ! -e /boot/home/config/settings/"$f"; done
rc=0
./probe lab off > result.csv 2> errors.txt || rc=$?
printf '%s\n' "$rc" > exit.txt
for f in result.csv errors.txt exit.txt; do curl -fsS -T "$f" http://10.0.2.2:8901/"$f"; done
