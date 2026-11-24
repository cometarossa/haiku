# IPC regression prefix replay
AI-assisted independent research fork. 3 repetitions each on V5, V7b
and V8 (last confirmed spin policy off), HVF, same three hash-verified
native binaries as the original regression. Replay copyerr, sweep 1/4/8
and shared/independent topology in the same order. Unlike the original
suite, upload each stage's stdout/stderr/exit code immediately, which
adds intervening network operations and timing differences. 54 stages
passed, 153,000 verified messages, no errors. Original intermittent
failure remains unresolved; no claim that the defect has been fixed.
Diagnostic topology source variant prepared separately, not compiled or
validated in this experiment. No kernel changes. Full paired V8 suite
and mixed-priority/TCG acceptance still pending.
