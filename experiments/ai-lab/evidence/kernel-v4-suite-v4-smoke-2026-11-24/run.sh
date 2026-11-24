#!/bin/sh
# AI-assisted independent Haiku fork. Run only in disposable lab guests.
# All executables must be transferred from the same verified host bundle.
set -eu
set -- 35eca30c http://10.0.2.2:8899
test "$#" = 2
revision=$1
url=$2
case "$revision" in 7d5672a7|35eca30c) ;; *) exit 2;; esac
case "$url" in http://10.0.2.2:8899) ;; *) exit 2;; esac
uname -a | grep "ai_$revision"
mkdir -p /boot/home/v4-acceptance
cd /boot/home/v4-acceptance
for f in copyerr sweep topology cost wake fair smode; do
    curl -fsS "$url/$f" -o "$f"
    chmod +x "$f"
done
curl -fsS "$url/SHA256SUMS" -o SHA256SUMS
sha256sum -c SHA256SUMS
test "$(./smode)" = 0
uname -a > revision.txt
./copyerr > copyerr.csv
for n in 1 4 8; do
    ./sweep "$n" 16 > "sweep-$n.csv"
done
printf 'mode,pairs,ports,verified,joined,errors,elapsed_us\n' > topology.csv
for mode in shared independent; do
    ./topology "$mode" >> topology.csv
done
./cost > cost.csv
printf 'scheduler_mode,priority,load_threads,round,lateness_us\n' > wake.csv
for p in 10 15; do
    for n in 0 2; do
        ./wake "$p" "$n" >> wake.csv
    done
done
printf 'cpus,worker,cpu,batches,digest,start_offset_us,end_offset_us\n' > fair.csv
for n in 1 4; do
    ./fair "$n" >> fair.csv
done
for f in revision.txt copyerr.csv sweep-1.csv sweep-4.csv sweep-8.csv topology.csv cost.csv wake.csv fair.csv; do
    curl -fsS -T "$f" "$url/$f"
done
printf 'PASS\n' > result.txt
curl -fsS -T result.txt "$url/result.txt"
