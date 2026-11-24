#!/bin/sh
set -eu
cd /boot/home
curl -fsS http://10.0.2.2:8899/kernel.cpp -o kernel.cpp
g++ -std=c++11 -O2 -Wall -Wextra -o kernel_probe kernel.cpp -lbe
for n in 1 4 8; do
 ./kernel_probe "$n" > "kernel-$n.csv"
 cat "kernel-$n.csv"
 curl -fsS -T "kernel-$n.csv" http://10.0.2.2:8899/kernel-$n.csv
done
echo KERNEL_PROBE_PASS
