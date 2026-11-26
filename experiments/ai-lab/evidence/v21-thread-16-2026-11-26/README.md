# V21 sixteen-stream decoder parallelism
Image 2f9d27bf, 4 vCPU, 8192 MiB. All four trials completed and
passed diagnostics, none passed playback. Deferred/catch-up OFF.
OFF 22967/31386 gap timeouts, ON 17901/30370.
OFF 6312 versus ON 9496 draw submissions; both pairs increase.
Successful queries 33/288 versus 67/288; lock failures 1567 versus
2344. All timeouts attributed to frame-gap policy.
Controller timeline samples incomplete in saturated runs; no claim
of full-speed playback or presentation FPS. Non-isolated host.
Treatment stays opt-in. Next compare deferred rendering OFF/ON
with single-thread decoding fixed on the same V21 image, starting
at four streams. This is exploratory, not promotion.
