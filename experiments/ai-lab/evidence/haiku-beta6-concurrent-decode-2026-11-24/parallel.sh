#!/bin/sh
# AI-assisted fork lab: baseline only, bounded concurrent decode.
set -eu
cd /boot/home
test -x ./media_decode
test -s t.mp4
mkdir -p concurrent-decode-20261124
cd concurrent-decode-20261124
printf 'streams,worker,status,frames,width,height,format,hash_fnv1a64\n' > parallel.csv
for n in 2 4; do
    pids=''
    i=1
    while [ "$i" -le "$n" ]; do
        (../media_decode ../t.mp4 > "$n-$i.csv" 2> "$n-$i.err") &
        pids="$pids $!"
        i=$((i+1))
    done
    i=1
    for pid in $pids; do
        status=0
        wait "$pid" || status=$?
        row=$(sed -n '2p' "$n-$i.csv")
        printf '%s,%s,%s,%s\n' "$n" "$i" "$status" "$row" >> parallel.csv
        i=$((i+1))
    done
    echo "Finished $n concurrent decoders"
done
cat parallel.csv
curl -fsS --connect-timeout 5 -T parallel.csv http://10.0.2.2:8899/parallel.csv
