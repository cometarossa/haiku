# AI-assisted independent research fork.
from pathlib import Path
import csv,statistics as st,re,hashlib,shutil
base=Path.home()/'Developer/Haiku/guest-results'
root=base/'v8-ab-20261124'
dst=Path('experiments/ai-lab/evidence/kernel-v8-ab-2026-11-24')
assert not dst.exists()
assert (root/'ready').read_bytes()==(base/'vm-area-teams-20261124/SHA256SUMS').read_bytes()
assert (root/'ready').read_text().split()[0]==hashlib.sha256((base/'vm-area-teams-20261124/vmt').read_bytes()).hexdigest()
def snaps(path):
 out=[]
 for line in path.read_text().splitlines():
  if not line.startswith('LAB_VMSPIN '):continue
  d={k:int(x) for k,x in re.findall(r'(\w+)=(\d+)',line)}
  assert set(d)=={'enabled','contended','acquired','fallback','spin_us'}
  assert d['contended']==d['acquired']+d['fallback']
  out.append(d)
 return out
assert snaps(root/'default.txt')==[dict(enabled=0,contended=0,acquired=0,fallback=0,spin_us=0)]
rows=[]; windows=[]
for rep in (1,2,3):
 for policy in ('off','on'):
  label=f'{policy}-{rep}'
  assert not (root/(label+'-errors.txt')).read_text().strip()
  a,b=snaps(root/(label+'.txt'))
  assert (a['enabled'],b['enabled'])==(int(policy=='on'),0)
  d={k:b[k]-a[k] for k in a if k!='enabled'}
  assert min(d.values())>=0 and d['contended']==d['acquired']+d['fallback']
  if policy=='off':assert not any(d.values())
  windows.append(dict(repeat=rep,policy=policy,**d))
  raw=list(csv.DictReader((root/(label+'.csv')).open()))
  assert len(raw)==32
  for pages in (256,1024):
   for cpus in (1,4):
    for mode in ('threads','teams'):
     sub=[r for r in raw if (r['mode'],int(r['pages']),int(r['cpus']))==(mode,pages,cpus)]
     assert len(sub)==4 and {int(r['worker']) for r in sub}==set(range(4))
     assert all(int(r['workers'])==4 and int(r['cpu'])==int(r['worker'])%cpus and int(r['checked'])==2*pages for r in sub)
     keys=('create_us','touch_us','warm_us','clone_us','verify_us','delete_us')
     assert all(int(r[k])>=0 for r in sub for k in keys)
     rows.append(dict(repeat=rep,policy=policy,mode=mode,pages=pages,cpus=cpus,checked=sum(int(r['checked']) for r in sub),**{k:st.median(int(r[k]) for r in sub) for k in keys}))
total=sum(r['checked'] for r in rows)
print('checks',total,'runs',len(rows),'worker rows',len(rows)*4)
for p in (256,1024):
 for c in (1,4):
  for m in ('threads','teams'):
   print(p,c,m,'touch_us',*[st.median(r['touch_us'] for r in rows if (r['pages'],r['cpus'],r['mode'],r['policy'])==(p,c,m,v)) for v in ('off','on')])
print(windows)
dst.mkdir()
for p in root.iterdir():
 if p.is_file():shutil.copyfile(p,dst/p.name)
for p in ('/tmp/haiku-v8-ab.py','/tmp/haiku-v8-ab-validate.py'):
 shutil.copyfile(p,dst/Path(p).name)
for name,values in [('summary.csv',rows),('spin-windows.csv',windows)]:
 with (dst/name).open('w') as f:
  w=csv.DictWriter(f,fieldnames=list(values[0]));w.writeheader();w.writerows(values)
(dst/'README.md').write_text(f"""# V8 initial HVF paired trylock experiment
AI-assisted independent research fork. Revision 752a2700, CI
45486033282. Separate overlay on Sequoia, 4 vCPU/8 GiB. Same
checksum-verified vmt executable; VM and mutex samplers disabled.
Three paired batches, off/on, on/off, off/on. Each batch has
eight workloads, 256/1024 pages, four workers in one or independent
teams, one/four vCPUs. {len(rows)} runs, {len(rows)*4} worker rows,
{total} alias/lifetime page checks passed. Retry policy disabled
after each batch. Spin snapshots cumulative, system-wide, include
other user-map activity and shell/debugger/transfer overhead.
Per-workload timing is median of four worker wall times; summary
comparison uses median of three batch medians. Not throughput or
bare-metal performance. Full acceptance (CPU/fairness/mixed
priority, IPC/scheduler regression, TCG, V7b off reference) pending.
Do not enable by default or purge reference images on this alone.
""")
(dst/'SHA256SUMS').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name+'\n' for p in sorted(dst.iterdir()) if p.is_file()))
