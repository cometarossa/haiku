#!/bin/sh
set -eu
cd /boot/home
uname -a | grep ai_7d5672a7
for f in smode wake; do curl -fsS http://10.0.2.2:8899/$f -o "$f"; chmod +x "$f"; done
curl -fsS http://10.0.2.2:8899/SHA256SUMS -o mode.sha256
sha256sum -c mode.sha256
original=$(./smode)
trap './smode "$original" >/dev/null' EXIT
trap 'exit 1' HUP INT TERM
printf 'repeat,scheduler_mode,priority,load_threads,round,lateness_us\n' > mode.csv
for rep in 1 2 3; do
 if test "$rep" = 2; then modes='1 0'; else modes='0 1'; fi
 for m in $modes; do
  ./smode "$m"
  sleep 1
  for p in 10 15; do
   for n in 0 2; do
    ./wake "$p" "$n" > one-mode.csv
    sed "s/^/$rep,/" one-mode.csv >> mode.csv
   done
  done
 done
done
restored=$(./smode "$original")
test "$restored" = "$original"
printf 'original=%s\nrestored=%s\n' "$original" "$restored" > restored.txt
trap - EXIT HUP INT TERM
curl -fsS -T restored.txt http://10.0.2.2:8899/restored.txt
curl -fsS -T mode.csv http://10.0.2.2:8899/v3.csv
wc -l mode.csv
