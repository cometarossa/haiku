# V21 native frame digest smoke
Image 2f9d27bf, probe source d087dfa7, checksum pinned in input manifest.
600 H.264 SD frames, 320x180 30fps, B_RGB32, every pixel digest
and presentation timestamp identical across OFF and ON.
FFmpeg thread_count configured 4->1, active_thread_type 1->0.
Elapsed decode + pixel hashing + initialization 1076121 ->384803 us.
One sequential pair, no isolation, possible warm-up/order effects.
No display FPS or broad codec correctness claim. Marker cleanup
verified by native script. Keep treatment opt-in; repeat paired
tests and verify lifecycle before escalating to simultaneous playback.
