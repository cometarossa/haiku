#!/bin/sh
# AI-assisted Haiku fork: conservative read-only workspace check.
set -eu

root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd -P)
cd "$root"
branch=$(git symbolic-ref --short HEAD)
revision=$(git rev-parse --short=12 HEAD)

printf 'Haiku source: %s\nBranch: %s\nRevision: %s\n' "$root" "$branch" "$revision"
if [ "$branch" != 'ai-experimental' ]; then
  printf '%s\n' 'ERROR: AI experiments only on ai-experimental branch' >&2
  exit 2
fi

probe_dir=$(mktemp -d "$root/.haiku-case-test.XXXXXXXX")
trap 'rm -rf "$probe_dir"' EXIT HUP INT TERM
printf A > "$probe_dir/Example"
printf B > "$probe_dir/example"
if [ ! -f "$probe_dir/Example" ] || [ ! -f "$probe_dir/example" ] ||
   [ "$(cat "$probe_dir/Example")" != A ]; then
  echo 'ERROR: filesystem is not case-sensitive' >&2
  exit 3
fi
echo 'Case-sensitive filesystem: OK'

for p in './data/catalogs/apps/screenshot/Screenshot/be.catkeys' \
         './data/catalogs/apps/screenshot/screenshot/be.catkeys' \
         './src/tests/kits/locale/CollatorTest.cpp' \
         './src/tests/kits/locale/collatorTest.cpp'; do
  if [ ! -f "$p" ]; then
    printf 'ERROR: source path missing: %s\n' "$p" >&2
    exit 4
  fi
done
echo 'Case-colliding upstream paths: present'

if [ -d "$root/../buildtools/.git" ]; then
  printf 'Buildtools revision: %s\n' "$(git -C "$root/../buildtools" rev-parse --short=12 HEAD)"
else
  echo 'Buildtools: missing (no full system build yet)'
fi
echo 'Host free disk:'
df -h "$root" | tail -1
echo 'Source status:'
git status --short | head -20
echo 'Workspace check: PASS'
