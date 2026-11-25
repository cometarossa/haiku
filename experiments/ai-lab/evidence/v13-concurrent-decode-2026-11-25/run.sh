#!/bin/sh
set -eu
cd /boot/home
mkdir -p v13-concurrent-decode
cd v13-concurrent-decode
for f in media_decode t.mp4 SHA256SUMS; do curl -fsS --max-time 30 http://10.0.2.2:8901/"$f" -o "$f"; done
sha256sum -c SHA256SUMS
chmod +x media_decode
uname -a > revision.txt
printf 'streams,worker,status,frames,width,height,format,hash_fnv1a64\n' > parallel.csv
for n in 1 2 4; do
 pids='';i=1
 while test "$i" -le "$n"; do
  (./media_decode t.mp4 > "$n-$i.csv" 2> "$n-$i.err") &
  pids="$pids $!";i=$((i+1))
 done
 i=1
 for pid in $pids; do
  rc=0;wait "$pid" || rc=$?
  row=$(sed -n '2p' "$n-$i.csv")
  printf '%s,%s,%s,%s\n' "$n" "$i" "$rc" "$row" >> parallel.csv
  for f in "$n-$i.csv" "$n-$i.err"; do curl -fsS -T "$f" http://10.0.2.2:8901/"$f"; done
  i=$((i+1))
 done
done
for f in revision.txt parallel.csv; do curl -fsS -T "$f" http://10.0.2.2:8901/"$f"; done
