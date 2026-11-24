from pathlib import Path
from http.server import HTTPServer,BaseHTTPRequestHandler
from threading import Thread
from subprocess import run
import hashlib,time,re
base=Path.home()/'Developer/Haiku'
root=base/'guest-results/v7b-handoff-repeat-20261124';root.mkdir(exist_ok=False)
binary=base/'guest-results/vm-area-teams-20261124/vmt'
raw=binary.read_bytes()
manifest=(hashlib.sha256(raw).hexdigest()+'  vmt\n').encode()
assert manifest==(binary.parent/'SHA256SUMS').read_bytes()
log=base/'ai-images/run-45444127880/haiku-ai-regular-serial.log'
setup=b'''#!/bin/sh
set -eu
cd /boot/home
uname -a | grep ai_34258af0
curl -fsS http://10.0.2.2:8899/vmt -o vmt
curl -fsS http://10.0.2.2:8899/SHA256SUMS -o vmt.sha256
sha256sum -c vmt.sha256
chmod +x vmt
curl -fsS http://10.0.2.2:8899/work.sh -o v7bwork.sh
curl -fsS -T vmt.sha256 http://10.0.2.2:8899/ready
'''
work=b'''#!/bin/sh
set -eu
cd /boot/home
if test "$1" = idle; then
 sleep 2
 printf 'idle complete\n' > v7brow.csv
else
 ./vmt "$1" 256 "$2" > v7brow.csv
fi
curl -fsS -T v7brow.csv "http://10.0.2.2:8899/$3.csv"
'''
(root/'setup.sh').write_bytes(setup);(root/'work.sh').write_bytes(work)
class H(BaseHTTPRequestHandler):
 def do_GET(self):
  data={'vmt':raw,'SHA256SUMS':manifest,'setup.sh':setup,'work.sh':work}.get(self.path[1:])
  if data is None:self.send_error(404);return
  self.send_response(200);self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
 def do_PUT(self):
  n=self.path[1:]
  if n!='ready' and not re.fullmatch(r'(idle|threads|teams)-[14]-[123]\.csv',n):self.send_error(404);return
  size=int(self.headers.get('Content-Length','0'))
  if not 0<=size<100000:self.send_error(400);return
  data=self.rfile.read(size);assert len(data)==size
  (root/n).write_bytes(data);self.send_response(201);self.end_headers()
s=HTTPServer(('127.0.0.1',8899),H);t=Thread(target=s.serve_forever,daemon=True);t.start()
h=['python3','experiments/ai-lab/guest-hmp.py','--run-id','45444127880']
def type_(v):run(h+['type',v],check=True,stdout=-3)
def wait_file(name,seconds=30):
 for _ in range(seconds*5):
  if (root/name).exists():return
  time.sleep(.2)
 raise RuntimeError(name+' missing')
def snap(mode):
 offset=log.stat().st_size
 type_('kernel_debugger')
 time.sleep(.6)
 try:
  type_('lab_vmstats'+(' '+mode if mode else ''))
  type_('lab_mutexstats'+(' '+mode if mode else ''))
  for _ in range(30):
   txt=log.read_bytes()[offset:].decode(errors='replace')
   if 'LAB_MUTEX_RESUME us=' in txt and 'ge1ms=' in txt.split('LAB_MUTEX_RESUME us=')[-1]:break
   time.sleep(.2)
  else:raise RuntimeError('snapshot missing '+txt[-500:])
 finally:
  type_('continue')
 time.sleep(.4)
 lines='\n'.join(line for line in txt.splitlines() if line.startswith(('LAB_VM','LAB_MUTEX')))+'\n'
 assert len(lines.splitlines())==7,lines
 return lines
try:
 type_('curl -fsS http://10.0.2.2:8899/setup.sh -o v7bsetup.sh')
 type_('sh v7bsetup.sh');wait_file('ready')
 assert (root/'ready').read_bytes()==manifest
 default=snap('')
 assert 'LAB_VM enabled=0 ' in default and 'LAB_MUTEX enabled=0 ' in default
 (root/'default.txt').write_text(default)
 for rep in (2,3):
  cases=[('threads',4),('teams',4),('threads',1)]
  if rep==2:cases.reverse()
  for mode,cpu in cases:
   label=f'{mode}-{cpu}-{rep}'
   before=snap('on')
   try:
    type_(f'sh /boot/home/v7bwork.sh {mode} {cpu} {label}')
    wait_file(label+'.csv')
   finally:
    after=snap('off')
    (root/(label+'.txt')).write_text(before+after)
   print(label,after.strip().replace('\n','; '),flush=True)
finally:
 s.shutdown();s.server_close();t.join()
