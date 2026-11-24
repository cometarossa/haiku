#!/bin/sh
set -eu
cd /boot/home
uname -a > v3-uname.txt
grep ai_7d5672a7 v3-uname.txt
curl -fsS -T v3-uname.txt http://10.0.2.2:8899/uname.txt
curl -fsS http://10.0.2.2:8899/copyerr -o copyerr
curl -fsS http://10.0.2.2:8899/SHA256SUMS -o copyerr.sha256
sha256sum -c copyerr.sha256
chmod +x copyerr
./copyerr > copyerr.csv || test "$?" = 1
cat copyerr.csv
curl -fsS -T copyerr.csv http://10.0.2.2:8899/v3-copyerr.csv
