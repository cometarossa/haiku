#!/bin/sh
set -eu
cd /boot/home
curl -fsS http://10.0.2.2:8899/mode.cpp -o mode.cpp
g++ -std=c++11 -O2 -Wall -Wextra -o smode mode.cpp -lbe
curl -fsS -T smode http://10.0.2.2:8899/smode
