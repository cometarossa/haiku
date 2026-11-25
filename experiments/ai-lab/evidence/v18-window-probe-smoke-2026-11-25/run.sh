#!/bin/sh
set -eu
cd /boot/home
mkdir v18-window-probe-smoke
cd v18-window-probe-smoke
base=http://10.0.2.2:8901
app=application/x-vnd.Haiku-MediaPlayer
for m in haiku-lab-media-stats haiku-lab-media-overlay-preflight haiku-lab-media-catchup haiku-lab-media-catchup-adaptive haiku-lab-video-view-stats; do
 test ! -e "/boot/home/config/settings/$m"
done
if hey -o "$app" count Window >/dev/null 2>&1; then exit 4; fi
for f in media-window-probe stream-long-sd.mp4 SHA256SUMS; do curl -fsS "$base/$f" -o "$f"; done
sha256sum -c SHA256SUMS
chmod +x media-window-probe
uname -a > revision.txt
/boot/system/apps/MediaPlayer "$PWD/stream-long-sd.mp4" > player.stdout 2> player.stderr &
pid=$!
sleep 3
count=$(hey -o "$app" count Window)
test "$count" -le 40
: > windows.txt
i=0
while test "$i" -lt "$count"; do
 title=$(hey -o "$app" get Title of Window "$i" 2>/dev/null || true)
 if test "$title" = stream-long-sd.mp4; then printf '%s %s\n' "$i" "$title" >> windows.txt; fi
 i=$((i+1))
done
test "$(wc -l < windows.txt | tr -d ' ')" = 1
i=$(cut -d ' ' -f 1 windows.txt)
hey "$app" do Stop of Window "$i"
hey "$app" do Play of Window "$i"
rc=0
./media-window-probe windows.txt 10 > probe.stdout 2> probe.stderr || rc=$?
printf '%s\n' "$rc" > probe.exit
hey "$app" quit || true
for j in $(seq 1 10); do if ! kill -0 "$pid" 2>/dev/null; then break; fi; sleep 1; done
prc=125
if ! kill -0 "$pid" 2>/dev/null; then prc=0; wait "$pid" || prc=$?; fi
printf '%s\n' "$prc" > player.exit
for f in revision.txt windows.txt probe.stdout probe.stderr probe.exit player.stdout player.stderr player.exit; do curl -fsS -T "$f" "$base/$f"; done
