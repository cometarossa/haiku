#!/bin/sh
set -eu
cd /boot/home
uname -a | grep ai_d800dd54
curl -fsS http://10.0.2.2:8899/handoff -o handoff
curl -fsS http://10.0.2.2:8899/SHA256SUMS -o handoff.sha256
sha256sum -c handoff.sha256
chmod +x handoff
printf 'repeat,mode,round,rtt_us\n' > handoff.csv
for rep in 1 2 3; do
 if test "$rep" = 2; then modes='port sem'; else modes='sem port'; fi
 for mode in $modes; do
  ./handoff "$mode" > one.csv
  sed "s/^/$rep,/" one.csv >> handoff.csv
 done
done
wc -l handoff.csv
curl -fsS -T handoff.csv http://10.0.2.2:8899/v2.csv
