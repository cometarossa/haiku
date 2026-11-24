#!/bin/sh
set -eu
cd /boot/home
if test "$1" = idle; then
 sleep 2
 printf 'idle complete
' > v7row.csv
else
 ./vmt "$1" 1024 "$2" > v7row.csv
fi
curl -fsS -T v7row.csv "http://10.0.2.2:8899/$3.csv"
