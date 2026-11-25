#!/bin/sh
set -eu
cd /boot/home
mkdir -p bitmap-phases-lab
cd bitmap-phases-lab
curl -fsS http://10.0.2.2:8901/bitmap.cpp -o bitmap.cpp
g++ -std=c++11 -O2 -Wall -Wextra -DLAB_SETUP_PHASES -o bitmap bitmap.cpp -lbe > compile.log 2>&1
uname -a > revision.txt
g++ --version > compiler.txt
sha256sum bitmap > SHA256SUMS
for f in bitmap compile.log revision.txt compiler.txt SHA256SUMS; do curl -fsS -T "$f" http://10.0.2.2:8901/"$f"; done
