# V13 quiet balanced performance comparison
Same V13 image 97075eae, corrected native binary, 36 runs, 108 workers,
147456 fills, 7077888 final RGB checks, 28311552 initial byte checks.
No errors. 36 matched traced ack/skip records; quiet expected no trace.
Quiet vs OFF median paired lifecycle ratios: threads2 .8849, teams2
.6850, threads4 .5048, teams4 .5101. Quiet wins 10/12 lifecycle blocks
against OFF; 6/6 for four surfaces. Quiet setup improves against traced
in 10/12 blocks. Host not isolated, only three blocks per topology,
synthetic fixed aggregate drawing work. No general performance claim.
Quiet server wire and prefill verified separately. Client write audit
and quiet eligibility pending; default remains unchanged.
