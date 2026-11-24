# Degenerate scheduler latency estimate
AI-assisted independent research fork. Beta6 and V4 ai_35eca30c.
Same binary, checksum verified on V4. Four normal-range priorities
(5,10,15,20), zero or two normal-priority workers pinned to vCPU 0;
20 samples per condition per guest, 320 calls total. Every result was
100 us. Static inspection: for nonnegative thread counts and positive
effective priorities <=120 the original subtraction makes the count
nonpositive, so the lower clamp dominates. The estimate is a heuristic,
not a real-time guarantee. Potential effects on Media Kit event
scheduling require separate verification. Initial compilation failed
because of a malformed printf string; corrected before both valid runs.
