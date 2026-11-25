from pathlib import Path
import csv,statistics,hashlib,shutil
base=Path.home()/'Developer/Haiku/guest-results'
root=base/'drawing-fixed-work-corrected-20261125'
bad=base/'drawing-fixed-work-20261125'
dst=Path('experiments/ai-lab/evidence/appserver-fixed-work-2026-11-25')
assert not dst.exists()
for folder in (root,bad):
 assert (folder/'SHA256SUMS').read_text()==hashlib.sha256((folder/'bitmap').read_bytes()).hexdigest()+'  bitmap\n'
rows=[];total=0;run_count=0
for ver,sha in [('beta',None),('v8','752a2700'),('v9','87d37528')]:
 rev=(root/(ver+'-revision.txt')).read_text()
 assert ('ai_'+sha in rev) if sha else ('beta6' in rev and 'ai_' not in rev),rev
 assert not (root/(ver+'-errors.txt')).read_text().strip()
 raw=list(csv.DictReader((root/(ver+'-results.csv')).open()))
 assert len(raw)==126,len(raw)
 total+=len(raw)
 for mode in ('threads','teams'):
  for n in (1,2,4):
   for b in (1,64,1024):
    times=[];skews=[]
    for rep in (1,2,3):
     a=[r for r in raw if (r['mode'],int(r['workers']),int(r['batch']),int(r['repeat']))==(mode,n,b,rep)]
     assert len(a)==n and {int(r['worker']) for r in a}==set(range(n))
     assert all([int(r[k]) for k in ('draws','checked','errors','exit')]==[4096//n,65536,0,0] for r in a)
     span={int(r['makespan_us']) for r in a};assert len(span)==1
     span=span.pop()
     assert min(int(r['start_us']) for r in a)==0 and max(int(r['end_us']) for r in a)==span
     assert all(0<=int(r['start_us'])<int(r['end_us'])<=span for r in a)
     times.append(span);skews.append(max(int(r['start_us']) for r in a));run_count+=1
    med=statistics.median(times)
    rows.append([ver,mode,n,b,*times,med,round(4096e6/med,2),max(skews)])
assert total==378 and run_count==162
dst.mkdir()
for p in root.iterdir():
 if p.is_file() and p.name!='bitmap':shutil.copyfile(p,dst/('binary-sha256.txt' if p.name=='SHA256SUMS' else p.name))
shutil.copyfile('/tmp/haiku-drawing-fixed-corrected.py',dst/'host-probe.py')
shutil.copyfile('/tmp/haiku-fixed-validate.py',dst/'validate.py')
invalid=dst/'excluded-malformed-output';invalid.mkdir()
for p in bad.iterdir():
 if p.is_file() and p.name!='bitmap':shutil.copyfile(p,invalid/('binary-sha256.txt' if p.name=='SHA256SUMS' else p.name))
shutil.copyfile('/tmp/haiku-drawing-fixed.py',invalid/'host-probe.py')
(invalid/'README.md').write_text('Excluded original run: C++ printf emitted literal backslash-n, so shell row prefixes and suffixes were not properly applied. Raw malformed CSV preserved. No timing or correctness claims derived from it. Corrected source recompiled and all runs repeated.\n')
with (dst/'summary.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['version','mode','surfaces','batch','run1_us','run2_us','run3_us','median_makespan_us','aggregate_fills_per_s','max_start_skew_us']);w.writerows(rows)
(dst/'README.md').write_text("""# Fixed-work concurrent offscreen rendering
AI-assisted independent research fork. Beta6/V8/V9, QEMU/HVF 4 vCPU/8 GiB.
Identical hash-verified native binary. 4096 fills total per run,
one/two/four independently owned 256x256 surfaces, with same-team
threads or separate BApplications in forked teams (fork before any GUI
objects); semaphore or pipe start barrier, respectively. Three repeats
per condition, Sync every 1/64/1024 fills. 162 runs, 378 worker rows,
663,552 fills, 24,772,608 final pixel checks, zero errors. Earliest
worker start to latest final Sync return; setup and final pixel scan
excluded, no affinity guarantee. Working set grows with number of
surfaces; verification volume increases with surfaces, not timed.
Host load uncontrolled, run order sequential; short batch timing noisy.
Excluded malformed first run and retained raw files. Corrected source
recompiled and all conditions rerun. Different barriers in threads vs
teams can contribute to start skew, recorded in raw data. Not native
hardware, compositing, GPU or frame-rate measurement.
Static inspection: OffscreenWindow creates its own DrawingEngine and
BitmapHWInterface, so no single shared drawing-engine instance;
ServerWindow::_MessageLooper also uses Desktop::LockSingleWindow
(shared read lock), and some messages use exclusive desktop lock.
This identifies candidate instrumentation sites, not causal proof.
Do not remove desktop locks without reviewing dispatch invariants.
No kernel or graphics server code modified. V8/V9 acceptance remains open.
""")
(dst/'SHA256SUMS').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p.relative_to(dst))+'\n' for p in sorted(dst.rglob('*')) if p.is_file()))
for r in rows: print(r)
print('VERIFIED',run_count,total,total*65536,run_count*4096)
