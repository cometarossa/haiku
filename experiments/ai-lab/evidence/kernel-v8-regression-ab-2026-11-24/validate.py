# AI-assisted independent research fork. Validate all raw native suite rows.
from pathlib import Path
import csv,statistics as st,math,re,hashlib,shutil
base=Path.home()/'Developer/Haiku/guest-results'
root=base/'v8-regression-ab-20261124'
dst=Path('experiments/ai-lab/evidence/kernel-v8-regression-ab-2026-11-24')
ref=base/'v5-regression-20261124'
assert not dst.exists()
mask=(1<<64)-1
def step(x):
 x^=(x<<13)&mask;x^=x>>7;x^=(x<<17)&mask
 return x
def apply(m,x):
 v=0
 while x:
  k=x&-x;v^=m[k.bit_length()-1];x^=k
 return v
powers=[tuple(step(1<<i) for i in range(64))]
for i in range(63):powers.append(tuple(apply(powers[-1],x) for x in powers[-1]))
def digest(n):
 x=1
 for i in range(n.bit_length()):
  if n>>i&1:x=apply(powers[i],x)
 return x
def read(p):return list(csv.DictReader(p.open()))
def ints(rows,keys):
 return [[int(r[k]) for k in keys] for r in rows]
def snap(p):
 a=[{k:int(v) for k,v in re.findall(r'(\w+)=(\d+)',x)} for x in p.read_text().splitlines() if x.startswith('LAB_VMSPIN ')]
 assert len(a)==2
 for d in a:assert set(d)=={'enabled','contended','acquired','fallback','spin_us'} and d['contended']==d['acquired']+d['fallback']
 return a
summary=[]
for rep in (1,2):
 for mode in ('off','on'):
  if rep==2 and mode=='off':continue
  label=f'{mode}-{rep}';p=root/label
  assert (p/'result.txt').read_text()=='PASS\n'
  assert 'ai_752a2700' in (p/'revision.txt').read_text()
  assert (p/'binary-sha256.txt').read_bytes()==(ref/'binary-sha256.txt').read_bytes()
  a,b=snap(root/(label+'-serial-complete.txt'));assert (a['enabled'],b['enabled'])==(int(mode=='on'),0)
  delta={k:b[k]-a[k] for k in a if k!='enabled'}
  assert min(delta.values())>=0 and delta['contended']==delta['acquired']+delta['fallback']
  if mode=='off':assert not any(delta.values())
  c=read(p/'copyerr.csv');assert len(c)==1
  assert c[0]['bad_status']==c[0]['expected_bad_address'] and c[0]['empty_status']==c[0]['expected_would_block'] and c[0]['pass']==c[0]['recovered']=='1'
  total=0;row=dict(repeat=rep,policy=mode,**delta)
  for n in (1,4,8):
   s=read(p/f'sweep-{n}.csv');assert len(s)==1
   r=s[0];assert ints(s,('threads','expected','received','shared_verified','joined','empty_timeout_ok','errors'))==[[n,n*1000,n*1000,n*1000,n,1,0]]
   total+=int(r['received']);row[f'sweep_{n}_us']=int(r['elapsed_us'])
  s=read(p/'topology.csv');assert len(s)==2 and {r['mode'] for r in s}=={'shared','independent'}
  for r in s:
   assert ints([r],('pairs','ports','verified','joined','errors'))==[[4,1 if r['mode']=='shared' else 4,2000,8,0]]
   total+=int(r['verified']);row[f'topology_{r["mode"]}_us']=int(r['elapsed_us'])
  s=read(p/'cost.csv');assert len(s)==18 and {(int(r['payload_bytes']),int(r['batch']),int(r['repeat'])) for r in s}=={(a,b,c) for a in (0,64,4096) for b in (1,64) for c in (1,2,3)}
  assert all(int(r['verified'])==4096 and int(r['errors'])==0 and int(r['elapsed_us'])>0 for r in s)
  total+=sum(int(r['verified']) for r in s);assert total==90728
  row['ipc_verified']=total
  for a in (0,64,4096):
   for b in (1,64):row[f'cost_{a}_{b}_us']=st.median(int(r['elapsed_us']) for r in s if int(r['payload_bytes'])==a and int(r['batch'])==b)
  s=read(p/'wake.csv');assert len(s)==480
  for priority in (10,15):
   for load in (0,2):
    sub=[r for r in s if int(r['priority'])==priority and int(r['load_threads'])==load]
    assert len(sub)==120 and {int(r['round']) for r in sub}==set(range(1,121)) and all(int(r['scheduler_mode'])==0 for r in sub)
    t=sorted(int(r['lateness_us']) for r in sub)
    row[f'wake_{priority}_{load}_p99_us']=t[math.ceil(.99*len(t))-1]
    row[f'wake_{priority}_{load}_max_us']=t[-1]
  s=read(p/'fair.csv');assert len(s)==8
  for cpu in (1,4):
   sub=[r for r in s if int(r['cpus'])==cpu];assert len(sub)==4 and {int(r['worker']) for r in sub}==set(range(4))
   batches=[]
   for r in sub:
    n=int(r['batches']);assert n>0 and int(r['cpu'])==int(r['worker'])%cpu
    assert digest(n*1024)==int(r['digest'])
    assert 0<=int(r['start_offset_us'])<int(r['end_offset_us'])
    batches.append(n)
   row[f'cpu_{cpu}_iterations']=sum(batches)*1024
   row[f'cpu_{cpu}_jain']=sum(batches)**2/(4*sum(n*n for n in batches))
  summary.append(row);print(label,'IPC',total,'P99',row['wake_10_2_p99_us'],row['wake_15_2_p99_us'],'CPU',row['cpu_1_iterations'],row['cpu_4_iterations'],flush=True)
failed=read(root/'off-2'/'topology.csv')
assert len(failed)==2 and ints(failed,('verified','joined','errors'))==[[2000,8,0],[0,0,9]]
assert not (root/'off-2'/'result.txt').exists()
print('FAILED off-2 topology',failed)
print('TOTAL',sum(r['ipc_verified'] for r in summary),len(summary)*480,len(summary)*8)
for k in summary[0]:
 if k in ('repeat','policy','ipc_verified','contended','acquired','fallback','spin_us'):continue
 a,b=(st.median(r[k] for r in summary if r['policy']==m) for m in ('off','on'))
 print(k,a,b,round((b/a-1)*100,2) if a else None)
dst.mkdir()
for p in root.iterdir():
 if p.is_dir():shutil.copytree(p,dst/p.name)
 else:shutil.copyfile(p,dst/p.name)
shutil.copyfile('/tmp/haiku-v8-reg-validate.py',dst/'validate.py')
with (dst/'summary.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(summary[0]));w.writeheader();w.writerows(summary)
(dst/'README.md').write_text("""# V8 native IPC/scheduler regression paired HVF smoke suite
AI-assisted independent research fork. V8 revision 752a2700, same
seven hash-verified ELF executables as V5. Three completed suites, interrupted at fourth (off-2). Each has 90,728 IPC checks, 480 wakeup samples, eight
CPU worker digests verified independently via GF(2) exponentiation.
Spin policy disabled after each suite. VM/mutex samplers remain off.
Three suites passed native correctness checks; the fourth failed in
independent IPC topology (0 verified, 0 joined, 9 errors). No fifth/sixth
suite attempted. Failed topology rows and serial tail retained; later
stale files were not recovered. Early log capture truncated a counter
line; full serial records matched captured prefixes and were retained.
No proof the failure is caused by V8: policy was off. Summary preserves raw
timings and fairness. Host load uncontrolled, no concurrent fault
storm, mixed-priority stress or TCG/native hardware gate here.
Unbalanced sample counts; not a completed A/B comparison or acceptance.
""")
(dst/'SHA256SUMS').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p.relative_to(dst))+'\n' for p in sorted(dst.rglob('*')) if p.is_file()))
