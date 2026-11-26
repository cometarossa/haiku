# V21 combined sixteen-stream campaign
Image 2f9d27bf, 4 vCPU/8192 MiB. Single-thread H264 SD fixed ON,
catch-up OFF, deferred rendering OFF/ON/ON/OFF.
All four trials diagnostic-valid, zero playback-valid.
OFF 23570/34031 vs ON 11762/28929 frame-gap timeouts;
7983 vs 3264 draw submissions; 1977 vs zero looper failures;
15 vs 31 successful queries out of 288. 13038 coalesces ON.
Queue means 230918/166357 us; handler means 5346/5533 us.
Both pairs lose substantial draw submissions. No presentation
FPS or overall performance acceptance. Host not isolated.
Next: GOP interval sensitivity, same V21 image, deferred OFF.
