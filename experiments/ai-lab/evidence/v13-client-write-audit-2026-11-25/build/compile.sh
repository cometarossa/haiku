#!/bin/sh
set -eu
cd /boot/home
mkdir -p bitmap-client-audit-build-retry
cd bitmap-client-audit-build-retry
for f in bitmap_client_audit.cpp bitmap_memset_audit.cpp; do curl -fsS http://10.0.2.2:8901/"$f" -o "$f"; done
rc=0
{ g++ -std=c++11 -O2 -Wall -Wextra -shared -fPIC -fno-builtin-memset -o audit.so bitmap_memset_audit.cpp && g++ -std=c++11 -O2 -Wall -Wextra -o audit bitmap_client_audit.cpp -lbe; } > compile.log 2>&1 || rc=$?
printf '%s\n' "$rc" > compile.exit
uname -a > revision.txt
for f in compile.log revision.txt compile.exit; do curl -fsS -T "$f" http://10.0.2.2:8901/"$f"; done
test "$rc" = 0
sha256sum audit audit.so > SHA256SUMS
for f in audit audit.so SHA256SUMS; do curl -fsS -T "$f" http://10.0.2.2:8901/"$f"; done
