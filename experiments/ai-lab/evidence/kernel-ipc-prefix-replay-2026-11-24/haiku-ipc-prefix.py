from pathlib import Path
from importlib import import_module
from http.server import HTTPServer,BaseHTTPRequestHandler
from threading import Thread
import subprocess as sp,sys,socket,time,hashlib,re
sys.path.insert(0,'experiments/ai-lab');h=import_module('guest-hmp')
base=Path.home()/'Developer/Haiku';root=base/'guest-results/ipc-prefix-replay-20261124';root.mkdir(exist_ok=False)
bundle={}
for name,folder in [('copyerr','ipc-sweep-20261124'),('sweep','ipc-sweep-20261124'),('topology','ipc-topology-20261124')]:
 p=base/'guest-results'/folder
 raw=(p/name).read_bytes()
 checksums={l.split()[1]:l.split()[0] for l in (p/'SHA256SUMS').read_text().splitlines()}
 assert hashlib.sha256(raw).hexdigest()==checksums[name]
 bundle[name]=raw
manifest=''.join(hashlib.sha256(raw).hexdigest()+'  '+name+'\n' for name,raw in sorted(bundle.items())).encode()
bundle['SHA256SUMS']=manifest
(root/'binary-sha256.txt').write_bytes(manifest)
script=b'''#!/bin/sh
set -eu
cd /boot/home
mkdir -p ipc-prefix-lab
cd ipc-prefix-lab
for f in copyerr sweep topology SHA256SUMS; do curl -fsS "http://10.0.2.2:8899/$f" -o "$f"; done
sha256sum -c SHA256SUMS
chmod +x copyerr sweep topology
uname -a > revision.txt
curl -fsS -T revision.txt "http://10.0.2.2:8899/$1-revision.txt"
for rep in 1 2 3; do
 for stage in copyerr sweep1 sweep4 sweep8 shared independent; do
  label="$1-$rep-$stage"
  rc=0
  case "$stage" in
   copyerr) ./copyerr >out.csv 2>err.txt || rc=$? ;;
   sweep1) ./sweep 1 16 >out.csv 2>err.txt || rc=$? ;;
   sweep4) ./sweep 4 16 >out.csv 2>err.txt || rc=$? ;;
   sweep8) ./sweep 8 16 >out.csv 2>err.txt || rc=$? ;;
   *) ./topology "$stage" >out.csv 2>err.txt || rc=$? ;;
  esac
  printf '%s\\n' "$rc" > rc.txt
  for f in out.csv err.txt rc.txt; do curl -fsS -T "$f" "http://10.0.2.2:8899/$label-$f"; done
 done
done
printf 'DONE\\n' > done.txt
curl -fsS -T done.txt "http://10.0.2.2:8899/$1-done.txt"
'''
bundle['work.sh']=script;(root/'work.sh').write_bytes(script)
class H(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_GET(self):
  data=bundle.get(self.path[1:])
  if data is None:self.send_error(404);return
  self.send_response(200);self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
 def do_PUT(self):
  n=self.path[1:];size=int(self.headers.get('Content-Length','0'))
  if not re.fullmatch(r'(v5|v7b|v8)-(revision\.txt|done\.txt|[123]-(copyerr|sweep1|sweep4|sweep8|shared|independent)-(out\.csv|err\.txt|rc\.txt))',n) or not 0<=size<100000:self.send_error(400);return
  data=self.rfile.read(size);assert len(data)==size
  assert not (root/n).exists()
  (root/n).write_bytes(data);self.send_response(201);self.end_headers()
  if n.endswith('-rc.txt'):print(n,data.decode().strip(),flush=True)
server=HTTPServer(('127.0.0.1',8899),H);t=Thread(target=server.serve_forever,daemon=True);t.start()
try:
 for v,r in [('v8','45486033282'),('v7b','45444127880'),('v5','45362378911')]:
  p=base/'ai-images'/('run-'+r)/'haiku-ai-regular-monitor.sock'
  with socket.socket(socket.AF_UNIX) as sock:
   sock.settimeout(8);sock.connect(str(p));h.receive_prompt(sock);h.exchange(sock,'mouse_move 10 10');time.sleep(.2);h.exchange(sock,'sendkey shift')
  cmd=['python3','experiments/ai-lab/guest-hmp.py','--run-id',r]
  sp.run(cmd+['type','curl -fsS http://10.0.2.2:8899/work.sh -o prefix.sh'],check=True)
  sp.run(cmd+['type','sh prefix.sh '+v],check=True)
  for _ in range(150):
   if (root/(v+'-done.txt')).exists():break
   time.sleep(1)
  else:raise RuntimeError(v+' incomplete')
  print(v,'completed',flush=True)
finally:server.shutdown();server.server_close();t.join()
