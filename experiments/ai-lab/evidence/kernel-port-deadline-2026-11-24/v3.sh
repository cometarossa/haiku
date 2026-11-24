#!/bin/sh
set -eu
cd /boot/home
uname -a | grep ai_7d5672a7
curl -fsS http://10.0.2.2:8899/deadline -o deadline
curl -fsS http://10.0.2.2:8899/SHA256SUMS -o deadline.sha256
sha256sum -c deadline.sha256
chmod +x deadline
./deadline > deadline.csv || test "$?" = 1
cat deadline.csv
curl -fsS -T deadline.csv http://10.0.2.2:8899/v3.csv
