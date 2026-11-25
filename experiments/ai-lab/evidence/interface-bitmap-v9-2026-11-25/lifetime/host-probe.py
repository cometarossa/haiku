from pathlib import Path
from importlib import import_module
from http.server import HTTPServer,BaseHTTPRequestHandler
from threading import Thread
import subprocess as sp,sys,socket,time,hashlib,re
sys.path.insert(0,'experiments/ai-lab');hmp=import_module('guest-hmp')
base=Path.home()/'Developer/Haiku'
root=base/'guest-results/bitmap-sync-v9-20261125';root.mkdir(exist_ok=True)
src=Path('experiments/ai-lab/desktop/bitmap_sync_lifetime.cpp').read_bytes()
scripts={}
for v in ('beta','v8','v9'):
 pre='#!/bin/sh\nset -eu\ncd /boot/home\nmkdir -p bitmap-v9-lab\ncd bitmap-v9-lab\n'
 if v=='beta':
  pre+='curl -fsS http://10.0.2.2:8899/bitmap.cpp -o bitmap.cpp\ng++ -std=c++11 -O2 -Wall -Wextra -o bitmap bitmap.cpp -lbe\ncurl -fsS -T bitmap http://10.0.2.2:8899/bitmap\n'
 else:
  pre+='for f in bitmap SHA256SUMS; do curl -fsS "http://10.0.2.2:8899/$f" -o "$f"; done\nsha256sum -c SHA256SUMS\nchmod +x bitmap\n'
 body="""uname -a > revision.txt
printf 'repeat,mode,draws,elapsed_us,checked,errors,exit\n' > results.csv
: > errors.txt
for rep in 1 2 3; do
 if test "$rep" = 2; then order='transaction direct'; else order='direct transaction'; fi
 for m in $order; do
  rc=0
  ./bitmap "$m" > one.csv 2>>errors.txt || rc=$?
  if test -s one.csv; then sed "s/^/$rep,/;s/$/,$rc/" one.csv >> results.csv; else echo "missing $rep $m rc=$rc" >> errors.txt; fi
 done
done
"""
 scripts[v+'.sh']=(pre+body+f'for f in revision.txt errors.txt results.csv; do curl -fsS -T "$f" "http://10.0.2.2:8899/{v}-$f"; done\n').encode()
 (root/(v+'.sh')).write_bytes(scripts[v+'.sh'])
class H(BaseHTTPRequestHandler):
 def do_GET(self):
  n=self.path[1:];data=src if n=='bitmap.cpp' else scripts.get(n)
  if data is None and n in ('bitmap','SHA256SUMS') and (root/n).is_file():data=(root/n).read_bytes()
  if data is None:self.send_error(404);return
  self.send_response(200);self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
 def do_PUT(self):
  n=self.path[1:];size=int(self.headers.get('Content-Length','0'))
  if not (n=='bitmap' or re.fullmatch(r'(beta|v8|v9)-(revision\.txt|errors\.txt|results\.csv)',n)) or not 0<=size<2000000:self.send_error(400);return
  data=self.rfile.read(size);assert len(data)==size
  (root/n).write_bytes(data);self.send_response(201);self.end_headers()
s=HTTPServer(('127.0.0.1',8899),H);t=Thread(target=s.serve_forever,daemon=True);t.start()
try:
 for v in sys.argv[1:]:
  target={'beta':['--baseline'],'v8':['--run-id','45486033282'],'v9':['--run-id','45504533141']}[v]
  p=base/'vm/haiku-ai-baseline-monitor.sock' if v=='beta' else base/'ai-images'/('run-'+target[1])/'haiku-ai-regular-monitor.sock'
  with socket.socket(socket.AF_UNIX) as sock:
   sock.settimeout(8);sock.connect(str(p));hmp.receive_prompt(sock);hmp.exchange(sock,'mouse_move 10 10');time.sleep(.2);hmp.exchange(sock,'sendkey shift')
  cmd=['python3','experiments/ai-lab/guest-hmp.py']+target
  assert not (root/(v+'-results.csv')).exists()
  sp.run(cmd+['type',f'curl -fsS http://10.0.2.2:8899/{v}.sh -o bitmaplab.sh'],check=True)
  sp.run(cmd+['type','sh bitmaplab.sh'],check=True)
  for _ in range(65):
   if (root/(v+'-results.csv')).exists():break
   time.sleep(1)
  else:raise RuntimeError(v+' incomplete')
  print(v,(root/(v+'-results.csv')).read_text(),(root/(v+'-errors.txt')).read_text(),flush=True)
  if v=='beta':(root/'SHA256SUMS').write_text(hashlib.sha256((root/'bitmap').read_bytes()).hexdigest()+'  bitmap\n')
finally:s.shutdown();s.server_close();t.join()
