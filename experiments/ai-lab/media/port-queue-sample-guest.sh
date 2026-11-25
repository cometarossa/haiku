#!/bin/sh
# Run as a separate, explicitly selected diagnostic workload, not in baseline A/B.
set -eu
test "$#" = 2
team="$1"
root="$2"
case "$team" in ''|*[!0-9]*) exit 2;; esac
test "$team" -gt 0
mkdir "$root"
command -v listport >/dev/null
# Bounded 20 samples, no global changes; snapshots are not atomic.
for i in $(seq 1 20); do
 stamp=$(system_time)
 (set -C; listport "$team" > "$root/port-$stamp.txt")
 sleep 1
done
