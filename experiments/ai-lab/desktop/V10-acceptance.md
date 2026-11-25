# V10: opt-in app_server per-window timing
AI-assisted independent research fork. No change to lock semantics,
protocol, dispatch order, drawing implementation or default policy.

Only offscreen ServerWindows of drawing_fixed_work.cpp are eligible
(signature exact threads or fixed- prefix teams). To opt in, create
/boot/home/config/settings/haiku-lab-appserver-profile in the disposable
guest overlay before launching the workload. Delete the marker to
disable for subsequently created windows. Existing windows retain their
initial state; ordinary applications never opt in. Not a security boundary.

Window-looper-local counters: acquisition wall time for own window
lock, Desktop read/write locks, total dispatch wall time, and subsets
AS_SYNC, AS_FILL_RECT, AS_VIEW_DRAW_BITMAP. Each records count, sum,
maximum and count >=50us. No cross-thread atomic counters, additional
clock reads or serial logging in the off path (some branches/local
initialization and opt-in check remain). On, two extra clock reads
per measured interval; timing includes scheduling and overhead, not
pure blocked time. Dispatch includes drawing and reply sends, but
not the initial IPC receive, desktop-lock acquisition or client wake.
Subset metrics must not be added to total dispatch. Per-window lifetime
includes setup and teardown commands; not exactly client timed interval.
Seven numeric rows and a completion marker per looper, emitted after
unlock at exit. Abnormal or missing records are rejected. Output itself
can perturb other concurrent windows near their completion.

Acceptance: x86_64 build, boot distinct overlay, default marker absent.
Transfer previously compiled fixed-work binary with SHA256 check.
Run 1/2/4 surfaces, threads/teams, batch 1/64/1024, >=3 alternate paired
repetitions, same V10 image, compare to V9 off. Use bounded per-run log
slices with full lines and expected window count and 4096 fills (verify
actual FillRect protocol mapping before interpreting if count differs).
Parser expects normal deletion and all seven phases; use 0 windows/
0 fills for off. Preserve raw logs, elapsed client timings, pixel checks,
host conditions, spin disabled, all failures. Quantify instrumentation
overhead before trusting timings. Remove marker at end even on failure.
No native test or speedup claimed by this source-only iteration.
