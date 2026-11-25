# V13 initial native MediaPlayer video smoke
Both existing synthetic fixtures pass guest SHA256 checks. Frame 04
shows stream-a at burned-in frame 20; frame 06 shows stream-b; frame 14
shows its playback position advancing. Terminal reports overlay buffer
allocation failure and fallback without overlays. No new serial text.
The two opens are not evidence of concurrent presentation: windows
overlap or are reused; attempted VNC separation was unsuccessful.
Audio absent; no FPS or dropped-frame claim. MediaPlayer VideoConsumer
uses overlay or B_BITMAP_IS_LOCKED, not the experimental white/view
flags or lab signature. This is compatibility smoke, not a V13 speed
comparison. Host ffprobe is unusable (missing libdav1d.6); use existing
hashed fixtures; no global Mac package changes.
