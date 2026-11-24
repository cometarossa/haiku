#!/bin/sh
set -eu
cd /boot/home
curl -fsS http://10.0.2.2:8899/deadline.cpp -o deadline.cpp
g++ -std=c++11 -O2 -Wall -Wextra -o deadline deadline.cpp -lbe
curl -fsS -T deadline http://10.0.2.2:8899/deadline
./deadline > deadline.csv || test "$?" = 1
cat deadline.csv
curl -fsS -T deadline.csv http://10.0.2.2:8899/beta.csv
