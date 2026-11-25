# V11b two-surface lifecycle extension
Same fddb1a1c image and native binary, batch64, fixed 4096 fills/run.
12 completed alternating OFF/ON runs, 24 worker rows, 49152 fills,
6291456 initial byte checks, 1572864 final RGB checks, 12 warm records.
No validation errors. Median total lifecycle worsens for both topologies
despite slightly faster rendering. Three observations per state; host
load uncontrolled; no causal or general performance claim.
Keep V11 disabled by default. V12 candidate: explicit server completion
acknowledgement to avoid the redundant client white fill.
