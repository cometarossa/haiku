# V21 combined eight-stream campaign
Image 2f9d27bf, 4 vCPU/8192 MiB. Single-thread H264 SD fixed ON,
catch-up OFF, deferred rendering OFF/ON/ON/OFF.
All four trials diagnostic- and playback-valid.
OFF 717/11213 vs ON 121/11666 frame-gap timeouts;
8128 vs 7693 draw submissions; 2148 vs zero looper failures;
146 vs 92 late consumer buffers. Position p95 improves in both
pairs (340970->108370 us; 222019->115722 us).
ON mean notification queue time 31492/23623 us; mean handler
time 4504/3155 us, 3583 coalesced notifications in total.
Controller timelines advance near realtime, not physical FPS.
Lifetime counts and two pairs; non-isolated host. Deferred path
improves measured responsiveness but draw submissions decrease.
No overall performance acceptance. Continue sixteen streams.
