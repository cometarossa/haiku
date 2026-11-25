# V16 HD native A/B: negative result
Same V16 image a1b69d83; numbered H.264 1280x720 at 30fps, 1200
frames, 40 seconds, no audio. Hash and ffprobe metadata retained.
Temporary RAMFS; 3 stable QEMU PIDs. 8/8 process exits zero but only
6/8 native trials meet validation. Four-window trials all pass without
activation or fill timeout. Eight-window OFF runs pass; both ON runs
fail playback samples, with ~46-47 s observation versus ~8 s intended.
Do not compare absolute counts or claim a win on timeout reduction.
The graphics target call accumulated time is high; cause not isolated.
The final done PUT was rejected (HTTP 400, stdin curl transfer without
Content-Length); collector stopped after all trial uploads. No synthetic
completion marker generated. Screenshot shows Terminal prompt and
the curl error. The scripts reached their final PUT after unmount.
Raw logs and invalid trials preserved. V17 proposed resolution gate
and backoff; no HD performance claim. Full screenshot set on host.
