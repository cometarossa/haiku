# Offscreen app_server draw/sync and IPC diagnostic smoke
AI-assisted independent research fork. Beta6, V5, V8 (spin policy
last confirmed off), QEMU/HVF. Two native binaries compiled on Beta6
and SHA256 checked on V5/V8. Offscreen B_RGB32 bitmap: 8 passes of
256 colored 16x16 tiles, 2048 FillRect calls plus SetHighColor calls;
Sync after 1, 64 or 2048 fills, 3 repeats. All 27 runs verified RGB
of all 65,536 final pixels (1,769,472 checks total). Intermediate
frames are not checked. Measured wall time includes client work,
server work and synchronous IPC; excludes bitmap setup and validation.
This contrasts existing API usage, not a kernel or app_server speedup.
Host load uncontrolled, substantial variance on V5; no GPU, onscreen
compositing, refresh rate, or bare-metal claims. IPC diagnostic variant
compiled and passed both topologies on each version: 6 runs, 12,000
verified messages, 48 joins and 48 per-worker detailed records.
Original intermittent failure remains unresolved. Next inspect Sync
and PortLink paths; retain semantics, then target redundant round
trips in OS code only where evidence supports it.
