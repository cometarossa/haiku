# V20 eight-stream diagnostic retry
Image 11904750; corrected ownership flags, explicit cleanup checks.
All four trials pass diagnostic and playback validation; final
completion marker after successful unmount. OFF 3369/10470 and
ON 458/11550 producer fill timeouts; every timeout matches an
explicit proxy frame-gap timeout; none propagated by seek/read.
OFF 5669 and ON 6982 draw submissions; 950 vs zero window lock
failures. ON 3930 coalesces. Cumulative queue 219588353 us and
handler 28448229 us across 6982 handlers, means 31.45 and 4.07 ms.
Position p95 OFF 2.593/288.278 ms, ON 117.393/106.566 ms.
Contrasts with V19 eight-stream regression; two pairs, non-isolated
host, instrumentation changed, no causal claim across versions.
Counts cover whole lifetimes, not physical display FPS.
Default remains OFF. Continue 16-stream diagnostic characterization.
