#!/bin/sh
set -eu
cd /boot/home
uname -a | grep ai_8f8e7d06
curl -fsS http://10.0.2.2:8899/mdp -o mdp
curl -fsS http://10.0.2.2:8899/SHA256SUMS -o mdp.sha256
sha256sum -c mdp.sha256
chmod +x mdp
printf 'priority,load_threads,mode,round,estimate_us,advance_us,error_us
' > mdp.csv
for p in 10 15 100 110; do
 for n in 0 2; do
  for mode in none estimate; do
   ./mdp "$p" "$n" "$mode" >> mdp.csv
  done
 done
done
curl -fsS -T mdp.csv http://10.0.2.2:8899/v5.csv
