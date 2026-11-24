#!/bin/sh
set -eu
cd /boot/home
uname -a | grep ai_752a2700
curl -fsS http://10.0.2.2:8899/vmt -o vmt
curl -fsS http://10.0.2.2:8899/SHA256SUMS -o vmt.sha256
sha256sum -c vmt.sha256
chmod +x vmt
curl -fsS http://10.0.2.2:8899/work.sh -o v8work.sh
curl -fsS -T vmt.sha256 http://10.0.2.2:8899/ready
