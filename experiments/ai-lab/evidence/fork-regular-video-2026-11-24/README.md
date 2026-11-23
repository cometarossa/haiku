# First full-fork video playback — 2026-11-24

AI-assisted research fork only. Regular desktop CI run 45285916285,
revision hrev60465+ai_d1e0b80c. QEMU/HVF, 4 vCPU, 8 GiB RAM.
After terminating the previously crashed MediaPlayer instance, the
native GUI opened the SHA256-verified test_video_h264.mp4 fixture.
The fixture is a 1280x720, 30 fps, 150-frame, five-second test pattern.
Screenshots show changing video content and burned-in frame indices
4 (0.133 s), 71 (2.367 s), and 138 (4.600 s). No new crash appeared
in the collected serial tail during this playback.

This establishes visible moving-video playback, not proof that all
150 frames were presented or that no frames were dropped. Audio,
concurrent GUI playback, performance, and the new single-frame
Controller fix (d800dd54) remain unverified in this guest. The new
regular build is separately in progress (run 45290072750).
