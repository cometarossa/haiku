# V8 native IPC/scheduler regression paired HVF smoke suite
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
