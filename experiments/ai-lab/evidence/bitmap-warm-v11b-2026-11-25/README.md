# V11b opt-in bitmap preparation smoke
AI-assisted independent research fork. Local build fddb1a1c, Zima 2 CPU
4 GiB cap, 382 seconds, 1045 targets, exit 0, no OOM. Both hashes
verified on Mac, revision confirmed by uname, desktop and Terminal.
Same native binaries as Beta6/V10 controls, HVF 4 vCPU/8 GiB.
Eligibility: 28 cases, 2 warm records only on eligible lab allocations
(256 KiB and exactly 1 MiB); zero for ordinary signature and OFF.
28 cases are not exhaustive coverage of overlay/clone/pressure.
Performance: 18 runs, 54 workers, 73728 fills, 14155776 initial byte
checks, 3538944 final RGB checks, 27 warm records, no errors.
3 OFF and 3 ON, batch64 only, one/four same-team workers and four
separate teams. Marker removed by each successful script. Initial
failed validation attempt preserved separately; tuple length mismatch
in host checker, guest exit 0; repeated entire performance campaign.
Lifecycle includes earliest bitmap constructor start to final drawing
Sync; includes initial scan and view setup, not destruction or process
start. Logging overhead and uncontrolled host load remain; small sample.
No broad claims, no page fault counters, no native GPU or compositing.
Do not enable optimization globally; full acceptance still pending.
