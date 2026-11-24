# Anonymous page placement experiment
AI-assisted independent research fork. Beta6 and V5 ai_8f8e7d06,
same checksum-verified binary. Four independent areas in one team;
four threads pinned to one or four virtual CPUs; affinity readback
and CPU residency checked before and after the touch loop. Three
repeats per condition, alternating placement order. 36 completed
runs, 144 worker rows, 129024 page-level alias checks, no errors.
First touch includes zero-check and writes; warm touch is a second
pass over resident pages. Timings are elapsed per worker, not
aggregate bandwidth. A large same-vCPU vs spread-vCPU gap occurs
on both versions; warm access remains much cheaper. This supports
investigation of page fault and cross-CPU translation synchronization
but does not establish a specific kernel lock or TLB cause. Host
load and QEMU/HVF overhead uncontrolled. Next isolate cross-team
address spaces and inspect x86 mapping/flush path before changing
invalidation semantics. No kernel source change in this experiment.
