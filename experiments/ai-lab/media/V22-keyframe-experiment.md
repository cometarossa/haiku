# V22 candidate: keyframe interval sensitivity, no OS change yet

ProxyVideoSupplier first asks MediaTrackVideoSupplier::SeekToFrame.
That supplier prefers the current decoder position if it lies between
the preceding keyframe and the target. Otherwise it seeks backward.
The proxy declines non-forced generation when the remaining gap
exceeds five frames. It can thus remain behind until a later keyframe.
The existing experimental bounded speculative recovery sometimes
helps SD but has regressed HD; do not simply raise the threshold.

Use two new fixtures derived from the same verified 120s SD source
(SHA256 08e5d9773d11247b52892dbbc42c9673c4db18cf4bab05f65c253a885c549a99).
ZimaBlade directory /DATA/Documents/haiku-ai-lab/fixtures-v22-gop.
Each uses FFmpeg libx264, High, yuv420p, 320x180, 30fps, 3600 frames,
no audio, preset fast, CRF18, two encoder threads and two B frames.
Generation:
    ffmpeg -nostdin -hide_banner -loglevel error -threads 1 -i "$src" \
      -map 0:v:0 -an -c:v libx264 -threads 2 -preset fast -crf 18 \
      -pix_fmt yuv420p -profile:v high -g "$g" -keyint_min "$g" \
      -sc_threshold 0 -bf 2 -x264-params open-gop=0 -movflags +faststart "gop-$g.mp4"
Use g=120 and g=15. Require ffprobe actual keyframe timestamps every
4 and 0.5 seconds, respectively, and pin both file checksums.
CRF controls quality, not exact bitrate or pixel equivalence;
changing GOP also changes frame types, size, and decoding cost.
Compare each file's native decoding and timestamps independently
before testing playback. Do not claim identical compressed streams
or isolate GOP from its intrinsic coding-complexity effects.

Keep same V21 image, vCPU/RAM, single-thread decoder ON and initially
deferred renderer OFF, speculative recovery OFF. Use balanced
long/short/short/long order, four streams first; then eight and
sixteen. Keep original long-SD fixture results as separate evidence.
Measure gap timeout fractions, max/mean gap, draw submissions and
valid responsiveness. A shorter GOP reducing timeouts supports
sensitivity to recovery distance, not a universal speedup. Do not
change the OS or default behavior based on this alone.
