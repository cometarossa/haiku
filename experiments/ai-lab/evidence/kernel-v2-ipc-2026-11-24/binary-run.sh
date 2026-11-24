#!/bin/sh
set -eu
cd /boot/home
uname -a | grep ai_d800dd54
curl -fsS http://10.0.2.2:8899/kernel_probe -o kernel_probe
curl -fsS http://10.0.2.2:8899/SHA256SUMS -o kernel.sha256
sha256sum -c kernel.sha256
chmod +x kernel_probe
for n in 1 4 8; do
 ./kernel_probe "$n" > "kernel-$n.csv"
 cat "kernel-$n.csv"
 curl -fsS -T "kernel-$n.csv" http://10.0.2.2:8899/kernel-$n.csv
done
echo KERNEL_V2_PASS
