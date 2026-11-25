# V18 native IPC queue sampling
V18 fb8c2e41, eight SD windows, persistent probe, diagnostics ON.
Ten listport samples during playback; app_server 40 ports, MediaPlayer
97. No sampled full queue. Maximum sampled relative depth 1% and 8%.
Samples span about 4.8 s, not the whole query interval; enumeration
is non-atomic and transient saturation remains possible. Probe 72/72
queries successful, median Position 152.4 ms, elapsed 12.44 s.
Not a paired comparison against the unsampled workload; sampling and
host scheduling may influence timing. All player exits zero,
RAMFS cleanup confirmed. Do not infer blocked-write duration or
change port capacities based on these samples.
