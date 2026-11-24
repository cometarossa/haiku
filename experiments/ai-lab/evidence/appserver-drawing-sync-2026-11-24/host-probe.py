from pathlib import Path
from http.server import HTTPServer,BaseHTTPRequestHandler
from threading import Thread
from subprocess import run
import hashlib,time,re
root=Path.home()/'Developer/Haiku/guest-results/appserver-sync-20261124';root.mkdir(exist_ok=False)
src={n:Path(p).read_bytes() for n,p in [('drawing.cpp','experiments/ai-lab/desktop/drawing_sync.cpp'),('topdiag.cpp','experiments/ai-lab/kernel/port_topology_diagnostic.cpp')]}
scripts={}
for v in ('beta','v5','v8'):
 pre='#!/bin/sh\nset -eu\ncd /boot/home\nmkdir -p drawing-lab\ncd drawing-lab\n'
 if v=='beta':
  pre+='for f in drawing.cpp topdiag.cpp; do curl -fsS "http://10.0.2.2:8899/$f" -o "$f"; done\n'
  pre+='g++ -std=c++11 -O2 -Wall -Wextra -o drawing drawing.cpp -lbe\ng++ -std=c++11 -O2 -Wall -Wextra -o topdiag topdiag.cpp -lbe\n'
  pre+='for f in drawing topdiag; do curl -fsS -T "$f" "http://10.0.2.2:8899/$f"; done\n'
 else:
  pre+='for f in drawing topdiag SHA256SUMS; do curl -fsS "http://10.0.2.2:8899/$f" -o "$f"; done\nsha256sum -c SHA256SUMS\nchmod +x drawing topdiag\n'
 body="""uname -a > revision.txt
printf 'repeat,batch,commands,syncs,elapsed_us,checked,errors,exit\\n' > draw.csv
: > draw-errors.txt
for rep in 1 2 3; do
 if test "$rep" = 2; then order='2048 64 1'; else order='1 64 2048'; fi
 for b in $order; do
  rc=0
  ./drawing "$b" > one.csv 2>>draw-errors.txt || rc=$?
  if test -s one.csv; then sed "s/^/$rep,/;s/$/,$rc/" one.csv >> draw.csv; else echo "missing $rep $b rc=$rc" >> draw-errors.txt; fi
 done
done
printf 'mode,pairs,ports,verified,joined,errors,elapsed_us,exit\\n' > topo.csv
: > topo-detail.txt
for m in shared independent; do
 rc=0
 ./topdiag "$m" > one.csv 2>>topo-detail.txt || rc=$?
 if test -s one.csv; then sed "s/$/,$rc/" one.csv >> topo.csv; else echo "missing $m rc=$rc" >> topo-detail.txt; fi
done
"""
 scripts[v+'.sh']=(pre+body+f'for f in revision.txt draw.csv draw-errors.txt topo.csv topo-detail.txt; do curl -fsS -T "$f" "http://10.0.2.2:8899/{v}-$f"; done\n').encode()
 (root/(v+'.sh')).write_bytes(scripts[v+'.sh'])
class H(BaseHTTPRequestHandler):
 def do_GET(self):
  n=self.path[1:];data=src.get(n,scripts.get(n))
  if data is None and n in ('drawing','topdiag','SHA256SUMS') and (root/n).is_file():data=(root/n).read_bytes()
  if data is None:self.send_error(404);return
  self.send_response(200);self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
 def do_PUT(self):
  n=self.path[1:];size=int(self.headers.get('Content-Length','0'))
  if not (n in ('drawing','topdiag') or re.fullmatch(r'(beta|v5|v8)-(revision\.txt|draw\.csv|draw-errors\.txt|topo\.csv|topo-detail\.txt)',n)) or not 0<=size<2000000:self.send_error(400);return
  data=self.rfile.read(size);assert len(data)==size
  (root/n).write_bytes(data);self.send_response(201);self.end_headers()
s=HTTPServer(('127.0.0.1',8899),H);t=Thread(target=s.serve_forever,daemon=True);t.start()
try:
 for v,target in [('beta',['--baseline']),('v5',['--run-id','45362378911']),('v8',['--run-id','45486033282'])]:
  h=['python3','experiments/ai-lab/guest-hmp.py']+target
  run(h+['type',f'curl -fsS http://10.0.2.2:8899/{v}.sh -o drawlab.sh'],check=True)
  run(h+['type','sh drawlab.sh'],check=True)
  for _ in range(90):
   if (root/(v+'-topo-detail.txt')).exists():break
   time.sleep(1)
  else:raise RuntimeError(v+' incomplete')
  print(v,(root/(v+'-draw.csv')).read_text(),(root/(v+'-draw-errors.txt')).read_text(),(root/(v+'-topo.csv')).read_text(),flush=True)
  if v=='beta':(root/'SHA256SUMS').write_text(''.join(hashlib.sha256((root/n).read_bytes()).hexdigest()+'  '+n+'\n' for n in ('drawing','topdiag')))
finally:s.shutdown();s.server_close();t.join()
