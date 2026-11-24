# Isolated IPC topology reproduction
AI-assisted independent research fork. Identical native binary and
SHA256 manifest as previous regression suites. V8 with spin policy
last confirmed off, V7b and V5 on HVF, 4 vCPU / 8 GiB. Ten shared and
ten independent-port runs per version, 60 runs / 120,000 verified
messages / 480 successful joins, no errors. Original off-2 failure
preserved in kernel-v8-regression-ab-2026-11-24. Not reproduced by
isolated topology workload; cannot conclude resolved or identify cause.
Original regression ran copyerr and three sweep processes before
topology. Next replay that prefix with per-stage exit statuses,
per-worker wait and return codes, and immediate raw uploads; compare
with a fresh process and baseline. Host load uncontrolled. No kernel
change, no performance acceptance, keep V8 opt-in disabled.
