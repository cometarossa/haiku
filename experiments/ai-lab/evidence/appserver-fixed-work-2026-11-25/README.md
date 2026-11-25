# Fixed-work concurrent offscreen rendering
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
