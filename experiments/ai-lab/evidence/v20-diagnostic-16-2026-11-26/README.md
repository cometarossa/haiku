# V20 sixteen-stream diagnostics
Image 11904750; OFF/ON/ON/OFF, fixed 20 s observation.
All four complete and diagnostic-valid, all four playback-invalid.
OFF 29831/43194 and ON 14900/25330 proxy gap timeouts.
Zero propagated seek/read timeouts, max gap 119 frames throughout.
OFF 11/288 successful queries and 10126 draws; ON 62/288
and 3243 draws. ON 6845 coalesces; queue elapsed 329922319 us,
handler elapsed 15939816 us across 3243 handlers.
All counters are lifetime data, not FPS or CPU time. Host not
isolated. Default OFF. V21 separately tests decoder parallelism;
no claim that thread oversubscription is the established cause.
