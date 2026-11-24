# V4 experimental scheduler acceptance

AI-assisted independent research fork only. This is a candidate, not a
performance claim. The only production-code change versus the V3 kernel
is the low-latency configuration (base 1000 -> 500 us, maximum latency
target 5000 -> 2500 us). Minimum quantum, multipliers and power-saving
mode stay unchanged. The maximum latency field is a tuning target,
not a real-time guarantee.

## Gate
- Build complete regular desktop image, verify both artifact hashes,
  boot a new disposable overlay; never overwrite V3 or persistent beta6.
- Confirm guest revision, scheduler mode 0, same QEMU/HVF CPU topology
  and RAM as V3; record host load, storage and competing VM state.
- Use the same checksum-verified executables on V3 and V4.
- Re-run port_copy_error, port_area_smp and port_topology for correctness.
- Run scheduler_wakeup (priorities 10 and 15, 0 and 2 load threads),
  at least three repeats in alternating V3/V4 order. Retain every sample.
- Run port_cost and port_topology for IPC throughput; add bounded
  CPU-bound throughput/fairness test on one and multiple vCPUs.
- Compare per-run median, P95, P99, missed 5ms periods and throughput.
  Do not accept a latency improvement bought with large throughput loss.
  Provisional targets: >=15% repeatable loaded P99 reduction, <=5%
  throughput loss, zero correctness failures. Report spread and all
  failures; inconclusive data leaves V3 as baseline.
- Never claim physical hardware speed from virtualized tests. Repeat
  under controlled host load and later on native hardware.
