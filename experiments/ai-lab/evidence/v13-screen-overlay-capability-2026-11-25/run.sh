#!/bin/sh
set -eu
cd /boot/home
screeninfo > v13-screeninfo.txt 2>&1
uname -a > v13-screeninfo-revision.txt
for f in v13-screeninfo.txt v13-screeninfo-revision.txt; do curl -fsS -T "$f" http://10.0.2.2:8901/"$f"; done
