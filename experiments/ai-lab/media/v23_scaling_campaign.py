"""Same-image scaling treatment, with recoverable original settings."""
from v23_scaling_smoke_runner import SHA,validate as validate_smoke
from v22_observation_smoke_report import analyze

def scaling_script(script,original_sha):
    if len(original_sha)!=64 or any(c not in "0123456789abcdef" for c in original_sha):
        raise ValueError("invalid original settings hash")
    changes=[
        (b'v22-observation-on-4-ram',b'v23-scaling-4-ram',2),
        (b'for f in stream-a.mp4 media-window-probe SHA256SUMS;',b'for f in stream-a.mp4 media-window-probe scaling-settings SHA256SUMS;',1),
        (b'chmod +x media-window-probe',b'chmod +x media-window-probe scaling-settings',1),
        (b'own_filltiming=0\ncleanup()',b'own_filltiming=0;own_scaling=0;pid=\ncleanup()',1),
        (b'cleanup() {',b'''cleanup() {
 if test "$own_scaling" = 1; then
  if test -n "$pid" && kill -0 "$pid" 2>/dev/null; then
   echo "Player still running; original saved at $backup/original" >&2; return 1
  fi
  if hey -o "$app" count Window >/dev/null 2>&1; then return 1; fi
  test -f "$backup/original" && test ! -L "$backup/original"
  test ! -L "$settings"
  if test -e "$settings"; then
   test -f "$settings" && test ! -e "$backup/final-generated"
   mv "$settings" "$backup/final-generated"
  fi
  mv "$backup/original" "$settings"
  own_scaling=0
  test "$(sha256sum "$settings" | awk '{print $1}')" = "$expected_settings"
 fi''',1),
        (b'run=0\nfor spec',b'''settings=/boot/home/config/settings/MediaPlayer
backup=/boot/home/v23-scaling-backup-4
expected_settings='''+original_sha.encode()+b'''
test -f "$settings" && test ! -L "$settings"
test "$(sha256sum "$settings" | awk '{print $1}')" = "$expected_settings"
if hey -o "$app" count Window >/dev/null 2>&1; then exit 4; fi
mkdir "$backup"
./scaling-settings "$settings" "$backup/variant-off" off
./scaling-settings "$settings" "$backup/variant-on" on
mv "$settings" "$backup/original"
own_scaling=1
run=0
for spec''',1),
        (b'if test "$st" = on; then (set -C; : > "$catchup"); c=1; fi',b'''test ! -e "$settings" && test ! -L "$settings"
 cp "$backup/variant-$st" "$settings"
 ./scaling-settings "$settings" > "$tag.scaling-before"
 curl -fsS -T "$tag.scaling-before" "$base/$tag.scaling-before"''',1),
        (b' test "$rc" = 0\n for i',b''' test "$rc" = 0
 pid=
 test -f "$settings" && test ! -L "$settings"
 ./scaling-settings "$settings" > "$tag.scaling-after"
 curl -fsS -T "$tag.scaling-after" "$base/$tag.scaling-after"
 mv "$settings" "$backup/after-$tag"
 for i''',1),
        (b'\ncleanup\nfor m',b'''\ncleanup
sha256sum "$settings" > settings-restored.txt
curl -fsS -T settings-restored.txt "$base/settings-restored.txt"
for m''',1),
    ]
    for old,new,count in changes:
        if script.count(old)!=count:raise ValueError("Unexpected scaling anchor: "+repr(old))
        script=script.replace(old,new)
    return script

def report(root,smoke):
    original=validate_smoke(smoke)
    r=analyze(root,"on",4,scaling=True)
    if r["complete"]:
        restored=(root/"settings-restored.txt").read_text().split()[0]
        if restored!=original["sha256"]:raise ValueError("original settings not restored")
    for row in r["rows"]:
        if not row["diagnostic_valid"]:continue
        expected="scaleBilinear="+("1" if row["state"]=="on" else "0")
        for ext in ("scaling-before","scaling-after"):
            if (root/(row["tag"]+"."+ext)).read_text().strip()!=expected:
                raise ValueError("scaling setting mismatch")
    return r
