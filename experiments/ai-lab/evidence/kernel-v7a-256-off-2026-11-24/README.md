# V7a smaller workload, diagnostics disabled
AI-assisted independent research fork. HVF guest hrev60465+ai_93d9c2d1.
Last KDL snapshot confirmed lab_vmstats off before this test.
Previously checksum-verified vm_area_teams native executable,
256 pages per worker, same or independent teams, one/four vCPUs,
three repeats, reverse order in repeat 2. 12 runs, 48 worker rows,
24576 alias/lifetime page checks, no reported errors.
This bounded off-state reference reproduces the shared address-space
slowdown without diagnostic counters enabled. Host load uncontrolled;
not a matched on/off comparison or native hardware evidence.
Use the identical workload in V7b to distinguish queue time from
handoff-to-return time. No tuning claim.
