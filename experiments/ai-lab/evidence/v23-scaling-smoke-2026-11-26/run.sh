#!/bin/sh
set -eu
cd /boot/home
mkdir v23-scaling-smoke
cd v23-scaling-smoke
base=http://10.0.2.2:8901
settings=/boot/home/config/settings/MediaPlayer
test -f "$settings" && test ! -L "$settings"
if hey -o application/x-vnd.Haiku-MediaPlayer count Window >/dev/null 2>&1; then exit 4; fi
curl -fsS "$base/scaling-settings" -o scaling-settings
curl -fsS "$base/SHA256SUMS" -o SHA256SUMS
sha256sum -c SHA256SUMS
chmod +x scaling-settings
cp "$settings" original
{
 uname -a
 printf 'original '; ./scaling-settings original
 printf 'nearest '; ./scaling-settings original nearest off
 printf 'bilinear '; ./scaling-settings nearest bilinear on
 printf 'nearest readback '; ./scaling-settings nearest
 printf 'bilinear readback '; ./scaling-settings bilinear
 if ./scaling-settings original nearest on; then exit 6; fi
 if ./scaling-settings original original off; then exit 7; fi
 printf 'exclusive output PASS\n'
 cmp "$settings" original
 printf 'active settings unchanged PASS\n'
 sha256sum original
 sha256sum "$settings"
} > smoke.txt
curl -fsS -T smoke.txt "$base/smoke.txt"
printf '0\n' > done.txt
curl -fsS -T done.txt "$base/done.txt"
