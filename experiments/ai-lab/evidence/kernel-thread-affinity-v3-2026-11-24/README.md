# V3 native affinity handoff comparison
AI-assisted independent research fork. V3 ai_7d5672a7, CI 45302538749.
Same beta6-compiled binary, SHA256 checked in guest and matched against
the earlier evidence. 6000 new V3 samples, 12000 total across both guests.
Same/split means vCPU 0/0 or 0/1, not physical cores. Both threads check
affinity and CPU placement. Fixed order, uncontrolled host load, separate
measurement times. No causal kernel speedup claim. Earlier failed attempts
had no CSV and were excluded: guest display blanking swallowed a first
keystroke; another attempt could not reach the temporary HTTP server.
After waking the guest and verifying shell focus, all transfers completed.
