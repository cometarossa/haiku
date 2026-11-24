#!/bin/sh
set -eu
cd /boot/home
mkdir -p ipc-prefix-lab
cd ipc-prefix-lab
for f in copyerr sweep topology SHA256SUMS; do curl -fsS "http://10.0.2.2:8899/$f" -o "$f"; done
sha256sum -c SHA256SUMS
chmod +x copyerr sweep topology
uname -a > revision.txt
curl -fsS -T revision.txt "http://10.0.2.2:8899/$1-revision.txt"
for rep in 1 2 3; do
 for stage in copyerr sweep1 sweep4 sweep8 shared independent; do
  label="$1-$rep-$stage"
  rc=0
  case "$stage" in
   copyerr) ./copyerr >out.csv 2>err.txt || rc=$? ;;
   sweep1) ./sweep 1 16 >out.csv 2>err.txt || rc=$? ;;
   sweep4) ./sweep 4 16 >out.csv 2>err.txt || rc=$? ;;
   sweep8) ./sweep 8 16 >out.csv 2>err.txt || rc=$? ;;
   *) ./topology "$stage" >out.csv 2>err.txt || rc=$? ;;
  esac
  printf '%s\n' "$rc" > rc.txt
  for f in out.csv err.txt rc.txt; do curl -fsS -T "$f" "http://10.0.2.2:8899/$label-$f"; done
 done
done
printf 'DONE\n' > done.txt
curl -fsS -T done.txt "http://10.0.2.2:8899/$1-done.txt"
