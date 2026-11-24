#!/bin/sh
set -eu
cd /boot/home
if test "$1" = idle; then
 sleep 2
 printf 'idle complete
' > v7brow.csv
else
 ./vmt "$1" 256 "$2" > v7brow.csv
fi
curl -fsS -T v7brow.csv "http://10.0.2.2:8899/$3.csv"
