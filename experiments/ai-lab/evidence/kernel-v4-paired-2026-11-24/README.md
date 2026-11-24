# Alternating V3/V4 scheduler comparison
AI-assisted independent research fork. Order V3,V4,V4,V3,V3,V4.
Six complete native guest suites, identical verified binary manifests.
544368 valid IPC messages, 2880 wakeup samples, 48 CPU worker rows.
Median of the three loaded run P99 values: normal 9991 -> 4836 us;
display 9646 -> 4882 us. Median nominal one-second CPU work:
1 vCPU 676938752 -> 672431104; 4 vCPUs 2570482688 -> 2475802624.
Numerical latency and CPU throughput thresholds pass on these medians.
Other guests and host activity remain uncontrolled; some individual
runs vary materially. No claim of bare-metal speed, full IPC throughput
gate, or production readiness. V4 remains the preferred experimental
candidate and V3 the reference. All raw runs preserved.
