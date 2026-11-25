# V12 complete setup phase diagnostic
36 runs, 108 workers, 147456 fills, 7077888 final RGB checks,
28311552 initial byte checks; no errors. Independent instrumented
binary, same image 5581c34f, balanced OFF/warm/single comparison.
The largest individual worker setup is attributed to actual phases,
not unrelated maxima. Median V12 constructor deltas (microseconds):
threads2 11457, teams2 10656, threads4 7977, teams4 17526.
Wall time, not CPU time; construction includes IPC, mapping, window
creation, and tracing. No causal claim. Host was not isolated.
