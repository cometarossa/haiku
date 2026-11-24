from pathlib import Path
import csv,hashlib,shutil
base=Path.home()/'Developer/Haiku/guest-results'
root=base/'ipc-prefix-replay-20261124'
dst=Path('experiments/ai-lab/evidence/kernel-ipc-prefix-replay-2026-11-24')
assert not dst.exists()
expected={n:hashlib.sha256((base/f/n).read_bytes()).hexdigest() for n,f in [('copyerr','ipc-sweep-20261124'),('sweep','ipc-sweep-20261124'),('topology','ipc-topology-20261124')]}
assert (root/'binary-sha256.txt').read_text()==''.join(expected[n]+'  '+n+'\n' for n in sorted(expected))
summary=[]
for v,sha in [('v5','8f8e7d06'),('v7b','34258af0'),('v8','752a2700')]:
 assert 'ai_'+sha in (root/(v+'-revision.txt')).read_text()
 assert (root/(v+'-done.txt')).read_text()=='DONE\n'
 for rep in (1,2,3):
  for stage in ('copyerr','sweep1','sweep4','sweep8','shared','independent'):
   label=f'{v}-{rep}-{stage}'
   rc=int((root/(label+'-rc.txt')).read_text());assert rc==0,label
   assert not (root/(label+'-err.txt')).read_text().strip(),label
   data=(root/(label+'-out.csv')).read_text()
   if stage=='copyerr':
    r=list(csv.DictReader(data.splitlines()));assert len(r)==1
    a=r[0];assert a['bad_status']==a['expected_bad_address'] and a['empty_status']==a['expected_would_block'] and a['recovered']==a['pass']=='1'
    n=0;elapsed=''
   elif stage.startswith('sweep'):
    r=list(csv.DictReader(data.splitlines()));assert len(r)==1
    a=r[0];k=int(stage[5:]);n=k*1000
    assert [int(a[x]) for x in ('threads','expected','received','shared_verified','joined','empty_timeout_ok','errors')]==[k,n,n,n,k,1,0]
    elapsed=int(a['elapsed_us'])
   else:
    r=list(csv.reader(data.splitlines()));assert len(r)==1
    a=r[0];n=2000
    assert a[0]==stage and list(map(int,a[1:6]))==[4,1 if stage=='shared' else 4,n,8,0]
    elapsed=int(a[6])
   summary.append([v,rep,stage,n,elapsed,rc])
assert len(summary)==54 and sum(r[3] for r in summary)==153000
dst.mkdir()
for p in root.iterdir():
 if p.is_file():shutil.copyfile(p,dst/p.name)
for f in ('haiku-ipc-prefix.py','haiku-ipc-prefix-validate.py'):
 shutil.copyfile('/tmp/'+f,dst/f)
with (dst/'summary.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['version','repeat','stage','verified','elapsed_us','exit']);w.writerows(summary)
(dst/'README.md').write_text("""# IPC regression prefix replay
AI-assisted independent research fork. 3 repetitions each on V5, V7b
and V8 (last confirmed spin policy off), HVF, same three hash-verified
native binaries as the original regression. Replay copyerr, sweep 1/4/8
and shared/independent topology in the same order. Unlike the original
suite, upload each stage's stdout/stderr/exit code immediately, which
adds intervening network operations and timing differences. 54 stages
passed, 153,000 verified messages, no errors. Original intermittent
failure remains unresolved; no claim that the defect has been fixed.
Diagnostic topology source variant prepared separately, not compiled or
validated in this experiment. No kernel changes. Full paired V8 suite
and mixed-priority/TCG acceptance still pending.
""")
(dst/'SHA256SUMS').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name+'\n' for p in sorted(dst.iterdir()) if p.is_file()))
print('Verified stages:',len(summary),'IPC messages:',sum(r[3] for r in summary))
