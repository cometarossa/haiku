#!/bin/sh
set -eu
cd /boot/home
uname -a | grep ai_93d9c2d1
curl -fsS http://10.0.2.2:8899/vmt -o vmt
curl -fsS http://10.0.2.2:8899/SHA256SUMS -o vmt.sha256
sha256sum -c vmt.sha256
chmod +x vmt
curl -fsS http://10.0.2.2:8899/work.sh -o v7work.sh
curl -fsS -T vmt.sha256 http://10.0.2.2:8899/ready
