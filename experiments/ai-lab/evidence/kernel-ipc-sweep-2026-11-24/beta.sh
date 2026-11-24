#!/bin/sh
set -eu
cd /boot/home
curl -fsS http://10.0.2.2:8899/port_area_smp.cpp -o sweep.cpp
curl -fsS http://10.0.2.2:8899/port_copy_error.cpp -o copyerr.cpp
g++ -std=c++11 -O2 -Wall -Wextra -o sweep sweep.cpp -lbe
g++ -std=c++11 -O2 -Wall -Wextra -o copyerr copyerr.cpp -lbe
for f in sweep copyerr; do curl -fsS -T "$f" http://10.0.2.2:8899/$f; done
./copyerr > copyerr.csv || test "$?" = 1
cat copyerr.csv
curl -fsS -T copyerr.csv http://10.0.2.2:8899/beta-copyerr.csv
for c in 16 64 256; do
 for n in 4 8; do
  ./sweep "$n" "$c" > sweep.csv
  cat sweep.csv
  curl -fsS -T sweep.csv http://10.0.2.2:8899/beta-$c-$n.csv
 done
done
echo SWEEP_BETA_DONE
