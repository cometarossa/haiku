#!/bin/sh
set -eu
cd /boot/home
curl -fsS http://10.0.2.2:8899/cost.cpp -o cost.cpp
g++ -std=c++11 -O2 -Wall -Wextra -o cost cost.cpp -lbe
curl -fsS -T cost http://10.0.2.2:8899/cost
./cost > cost.csv
cat cost.csv
curl -fsS -T cost.csv http://10.0.2.2:8899/beta.csv
