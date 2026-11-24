#!/bin/sh
set -eu
cd /boot/home
curl -fsS http://10.0.2.2:8899/mdp.cpp -o mdp.cpp
g++ -std=c++11 -O2 -Wall -Wextra -o mdp mdp.cpp -lbe
curl -fsS -T mdp http://10.0.2.2:8899/mdp
