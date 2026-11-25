# V15 native instrumentation smoke
Revision db20e3f2, independent QEMU overlay, 4 vCPU, 8 GiB.
Same fixture and preflight ON, stats OFF then ON; both players exit 0.
OFF no diagnostic records; ON producer and consumer conservation pass.
185 fills, 184 sent, 1 send error (B_MEDIA_BAD_DESTINATION, -2147467146),
178 handled, 177 target calls, 1 no target, 0 late at both stages.
No consumer memcpy bytes recorded. First target return 623049 us from
launch, not first physical presentation. Aggregate wait/request
5831331 us versus FillBuffer 55925 us; wait may reflect pacing,
backpressure or shutdown, not proof of wasted time. One fill error
and one lock timeout; not guaranteed lossless. Distinct lifetimes
and queued events prevent cross-stage conservation. Host not isolated;
single small synthetic clip, no audio, not a benchmark of improvement.
Marker absence verified after test.
