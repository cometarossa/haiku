# V15 diagnostic candidate
Opt-in marker /boot/home/config/settings/haiku-lab-media-stats.
One producer summary per generator lifetime and consumer summary after
Quit joins the control thread. No new per-frame output or locks.
Producer counts lock timeouts, late skips, buffer wait and FillBuffer
latency/outcomes, suppressed sends and errors. Consumer counts
_HandleBuffer outcomes, copy bytes/time and target calls/time.
Counters include startup/stop/seek; queued events discarded before
_HandleBuffer are excluded. Target call is not a completed draw or
physical presentation. First target time is absolute guest monotonic
time. No scheduling, buffer count, render or copy policy change.
Native build pending. Require record conservation and OFF/ON tests
with identical fixtures and 1/2/4/8 streams before any tuning.
