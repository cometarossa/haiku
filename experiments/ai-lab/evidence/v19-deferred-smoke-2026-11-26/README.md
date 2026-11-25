# V19 native lifecycle smoke
Image 067ee57e. Initial validator rejected seek to 28s after
requesting 30s, in BOTH modes. Independent ffprobe on ZimaBlade
verified SHA256 08e5d9773d11247b52892dbbc42c9673c4db18cf4bab05f65c253a885c549a99
and keyframes 0,4,8,12,16,20,24,28,32,36,... seconds
(ffprobe -v error -select_streams v:0 -skip_frame nokey
-show_entries frame=best_effort_timestamp_time -of csv=p=0).
MediaTrackVideoSupplier::SeekToFrame selects closest backward.
Corrected validator pins fixture SHA and 28s expected keyframe.
Both lifetimes pass stop, seek, resume, pause and orderly exit.
ON: 143 queued/handled/draw, no failures/coalesces/skips.
Screens 004 and 005 show ON frame 0 and frame 906 (30.200s).
No FPS or end-to-end speedup claim: SetBitmap work moved to looper.
This smoke does not prove concurrency safety under heavy load.
