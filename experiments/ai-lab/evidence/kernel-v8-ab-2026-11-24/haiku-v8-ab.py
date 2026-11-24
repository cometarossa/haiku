# AI-assisted independent research fork: paired V8 on/off guest runs.
from pathlib import Path
from http.server import HTTPServer,BaseHTTPRequestHandler
from threading import Thread
from subprocess import run
import hashlib,time,re
base=Path.home()/'Developer/Haiku'
root=base/'guest-results/v8-ab-20261124';root.mkdir(exist_ok=False)
binary=base/'guest-results/vm-area-teams-20261124/vmt'
raw=binary.read_bytes()
manifest=(hashlib.sha256(raw).hexdigest()+'  vmt\n').encode()
assert manifest==(binary.parent/'SHA256SUMS').read_bytes()
log=base/'ai-images/run-45486033282/haiku-ai-regular-serial.log'
setup=b'''#!/bin/sh
set -eu
cd /boot/home
uname -a | grep ai_752a2700
curl -fsS http://10.0.2.2:8899/vmt -o vmt
curl -fsS http://10.0.2.2:8899/SHA256SUMS -o vmt.sha256
sha256sum -c vmt.sha256
chmod +x vmt
curl -fsS http://10.0.2.2:8899/work.sh -o v8work.sh
curl -fsS -T vmt.sha256 http://10.0.2.2:8899/ready
'''
work=b'''#!/bin/sh
set -eu
cd /boot/home
printf 'mode,workers,pages,cpus,worker,cpu,create_us,touch_us,warm_us,clone_us,verify_us,delete_us,checked\n' > v8row.csv
: > v8err.txt
for p in 256 1024; do
 for c in 1 4; do
  for m in threads teams; do
   if ./vmt "$m" "$p" "$c" > v8one.csv 2>>v8err.txt; then
    cat v8one.csv >> v8row.csv
   else
    echo "failed $m $p $c" >> v8err.txt
   fi
  done
 done
done
curl -fsS -T v8err.txt "http://10.0.2.2:8899/$1-errors.txt"
curl -fsS -T v8row.csv "http://10.0.2.2:8899/$1.csv"
'''
(root/'setup.sh').write_bytes(setup);(root/'work.sh').write_bytes(work)
class H(BaseHTTPRequestHandler):
 def do_GET(self):
  data={'vmt':raw,'SHA256SUMS':manifest,'setup.sh':setup,'work.sh':work}.get(self.path[1:])
  if data is None:self.send_error(404);return
  self.send_response(200);self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
 def do_PUT(self):
  n=self.path[1:]
  if n!='ready' and not re.fullmatch(r'(on|off)-[123](\.csv|-errors\.txt)',n):self.send_error(404);return
  size=int(self.headers.get('Content-Length','0'))
  if not 0<=size<100000:self.send_error(400);return
  data=self.rfile.read(size);assert len(data)==size
  (root/n).write_bytes(data);self.send_response(201);self.end_headers()
s=HTTPServer(('127.0.0.1',8899),H);t=Thread(target=s.serve_forever,daemon=True);t.start()
h=['python3','experiments/ai-lab/guest-hmp.py','--run-id','45486033282']
def type_(v):run(h+['type',v],check=True,stdout=-3)
def wait_file(name,seconds=90):
 for _ in range(seconds*5):
  if (root/name).exists():return
  time.sleep(.2)
 raise RuntimeError(name+' missing')
def snap(mode,initial=False):
 offset=log.stat().st_size
 type_('kernel_debugger')
 time.sleep(.6)
 try:
  if initial:
   type_('lab_vmstats')
   type_('lab_mutexstats')
  type_('lab_vmspin'+(' '+mode if mode else ''))
  for _ in range(40):
   txt=log.read_bytes()[offset:].decode(errors='replace')
   if 'LAB_VMSPIN enabled=' in txt and 'spin_us=' in txt.split('LAB_VMSPIN enabled=')[-1]:break
   time.sleep(.2)
  else:raise RuntimeError('snapshot missing '+txt[-500:])
 finally:
  type_('continue')
 time.sleep(.4)
 lines='\n'.join(line for line in txt.splitlines() if line.startswith(('LAB_VM','LAB_MUTEX')))+'\n'
 assert len(lines.splitlines())==(8 if initial else 1),lines
 if initial:
  assert 'LAB_VM enabled=0 ' in lines and 'LAB_MUTEX enabled=0 ' in lines
 return lines
try:
 type_('curl -fsS http://10.0.2.2:8899/setup.sh -o v8setup.sh')
 type_('sh v8setup.sh');wait_file('ready',30)
 assert (root/'ready').read_bytes()==manifest
 default=snap('',True)
 assert 'LAB_VMSPIN enabled=0 contended=0 acquired=0 fallback=0 spin_us=0' in default
 (root/'default.txt').write_text(default)
 for rep in (1,2,3):
  for mode in (('off','on') if rep!=2 else ('on','off')):
   label=f'{mode}-{rep}'
   before=snap(mode)
   try:
    type_(f'sh /boot/home/v8work.sh {label}')
    wait_file(label+'.csv')
   finally:
    after=snap('off')
    (root/(label+'.txt')).write_text(before+after)
   assert not (root/(label+'-errors.txt')).read_text().strip()
   print(label,'rows',len((root/(label+'.csv')).read_text().splitlines())-1,after.strip(),flush=True)
finally:
 s.shutdown();s.server_close();t.join()
