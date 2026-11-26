# V22 sixteen-stream teardown confound
Observed on V21 image, V22 GOP comparison, after three trials.
Host file modification times measure receipt, not guest exit.
Elapsed from host receipt of stop to exit upload: 20.34 s
(GOP120 first), 122.87 s and 123.89 s (GOP15). The stop
timestamp precedes quit request by about 1.2 guest seconds.
Final uploads may add delay; cannot separate quit RPC, process
shutdown, clock effects or transfer time with these old logs.
Producer dropped-frame records reach performance time 57.2 s,
143.67 s and 144.7 s respectively, while guest start-to-quit
intervals are 52.74, 51.37 and 52.84 s. Producer timeline is
not a wall clock; individual thread identities are absent here.
Do not infer a particular clock defect from these observations.

The 4.96x raw draw count in the first pair is a lifetime count
with substantial teardown confounding, not observation throughput.
Probe responsiveness is poor during the actual observation in
both GOP15 runs (1 and 2 successful queries of 144 expected).
Frame-gap fractions also cover the whole producer lifetime.
No claim of graphical or decoding speedup under this workload.

New runner records guest quit-request, quit-return and exit-time,
uploads quit-request before the quit call; paired analysis now
withholds lifetime-normalized draw rates when exit clocks absent.
Earlier archived normalized rates used start-to-quit-request time
and should not be used as throughput measurements. Preserve raw
evidence unchanged. Future observation-window counters need
explicit phase boundaries inside native code; no such counters
exist yet. No change to the image or active test.
