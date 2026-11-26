#!/bin/sh
set -eu
cd /boot/home
base=http://10.0.2.2:8901
app=application/x-vnd.Haiku-MediaPlayer
if hey -o "$app" count Window >/dev/null 2>&1; then exit 4; fi
settings=/boot/home/config/settings
proxy="$settings/haiku-lab-video-proxy-stats"
{
 uname -a
 ls -ld "$proxy"
 for m in haiku-lab-media-stats haiku-lab-media-overlay-preflight haiku-lab-video-view-stats haiku-lab-video-deferred haiku-lab-video-deferred-timing haiku-lab-media-catchup haiku-lab-media-catchup-adaptive; do
  if test -e "$settings/$m" || test -L "$settings/$m"; then echo "unexpected $m"; exit 7; fi
 done
 test -f "$proxy" && test ! -L "$proxy" && test ! -s "$proxy"
 ls -la /boot/home/v20-diagnostic-8-ram
 rm -f "$proxy"
 unmount /boot/home/v20-diagnostic-8-ram
 mv /boot/home/v20-diagnostic-8-ram /boot/home/v20-diagnostic-8-ram-aborted
 test ! -e "$proxy" && test ! -L "$proxy"
 echo 'CLEANUP_OK'
} > /boot/home/v20-cleanup-audit.txt 2>&1
curl -fsS -T /boot/home/v20-cleanup-audit.txt "$base/audit.txt"
