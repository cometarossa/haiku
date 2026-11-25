#!/bin/sh
set -eu
cd /boot/home
mkdir -p bitmap-reply-v13-lab
cd bitmap-reply-v13-lab
curl -fsS http://10.0.2.2:8901/probe -o probe
curl -fsS http://10.0.2.2:8901/SHA256SUMS -o SHA256SUMS
sha256sum -c SHA256SUMS
chmod +x probe
settings=/boot/home/config/settings
warm=$settings/haiku-lab-bitmap-warm
single=$settings/haiku-lab-bitmap-single-clear
quiet=$settings/haiku-lab-bitmap-quiet
for m in "$warm" "$single" "$quiet"; do test ! -e "$m" && test ! -L "$m"; done
w=0;s=0;q=0
cleanup() {
 if test "$q" = 1; then rm -f "$quiet"; q=0; fi
 if test "$s" = 1; then rm -f "$single"; s=0; fi
 if test "$w" = 1; then rm -f "$warm"; w=0; fi
}
trap cleanup 0
trap 'exit 125' 1 2 15
uname -a > revision.txt
curl -fsS -T revision.txt http://10.0.2.2:8901/revision.txt
for state in off warm single quiet; do
 case "$state" in
 warm) (set -C; : > "$warm"); w=1 ;;
 single) (set -C; : > "$single"); s=1 ;;
 quiet) (set -C; : > "$single"); s=1; (set -C; : > "$quiet"); q=1 ;;
 esac
 for mode in lab ordinary; do
  p="$state-$mode"
  rc=0
  ./probe "$mode" "$state" > "$p.csv" 2> "$p.err" || rc=$?
  printf '%s\n' "$rc" > "$p.exit"
  for f in "$p.csv" "$p.err" "$p.exit"; do curl -fsS -T "$f" http://10.0.2.2:8901/"$f"; done
  test "$rc" = 0
 done
 cleanup
done
for m in "$warm" "$single" "$quiet"; do test ! -e "$m" && test ! -L "$m"; done
printf '0\n' > done.txt
curl -fsS -T done.txt http://10.0.2.2:8901/done.txt
