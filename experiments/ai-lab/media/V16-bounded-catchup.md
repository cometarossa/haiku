# V16 bounded catch-up experiment

V15 after host cleanup: four of eight producers account for all 909
FillBuffer timeout outcomes. Source audit: ProxyVideoSupplier abandons
non-forced requests when SeekToFrame leaves a gap larger than five.
MediaTrackVideoSupplier may reuse the current decoder position rather
than seek backward; without decoding, the gap can persist until a new
keyframe. This is a plausible mechanism, not a proven attribution of
every timeout (a track can also return B_TIMED_OUT).

Marker /boot/home/config/settings/haiku-lab-media-catchup enables an
experiment per ProxyVideoSupplier instance. On the existing gap-reject
path, when returned frame equals decoder position and is nonnegative,
decode at most five intermediate frames and stop starting additional
reads once 4000 us elapsed. This is a soft budget; any individual
ReadFrame call can exceed it. Abort the loop on error, no progress or
overshoot. Return the same B_TIMED_OUT, so no intermediate output is
submitted; subsequent requests can resume normal decoding. Forced
generation, short gap, cached frame, seek error paths unchanged.
One activation message per instance when forward progress occurs.

Host tests exercise actual FillBuffer source with fake track, including
OFF stalling, ON bounded progress, exact eventual requested output,
soft budget, no progress, error, mismatch, forced and ordinary cases.
These do not certify real decoder output or scheduling.

Native acceptance: same V16 image, V15 stats and overlay markers ON,
catch-up OFF/ON alternated, identical dynamic fixture, 4 and 8 windows,
at most 2 Haiku guests and record host load. Verify activation only ON,
all windows advance, exits zero, no increased errors, compare per-stage
timeout fractions and target calls at controlled durations. Inspect
numbered moving frames and independent correctness/seek/cover-art/audio
checks. Capture stdout and stderr separately to avoid log interleaving.
Do not claim physical FPS based on target calls. Keep opt-in pending
native evidence; no global scheduling or buffer count change.
