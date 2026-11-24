# V8 initial HVF paired trylock experiment
AI-assisted independent research fork. Revision 752a2700, CI
45486033282. Separate overlay on Sequoia, 4 vCPU/8 GiB. Same
checksum-verified vmt executable; VM and mutex samplers disabled.
Three paired batches, off/on, on/off, off/on. Each batch has
eight workloads, 256/1024 pages, four workers in one or independent
teams, one/four vCPUs. 48 runs, 192 worker rows,
245760 alias/lifetime page checks passed. Retry policy disabled
after each batch. Spin snapshots cumulative, system-wide, include
other user-map activity and shell/debugger/transfer overhead.
Per-workload timing is median of four worker wall times; summary
comparison uses median of three batch medians. Not throughput or
bare-metal performance. Full acceptance (CPU/fairness/mixed
priority, IPC/scheduler regression, TCG, V7b off reference) pending.
Do not enable by default or purge reference images on this alone.
