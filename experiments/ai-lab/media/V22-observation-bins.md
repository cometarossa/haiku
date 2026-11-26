# V22 observation-only completion counters
Opt-in marker /boot/home/config/settings/haiku-lab-video-observation,
also requires existing media/view stats (or deferred treatment).
Absolute monotonic 1-second bins; 512 bins per instrumented lifetime,
32 KiB allocated only when enabled. No per-frame disk I/O, additional
locks, or per-frame logs. Overflow and allocation failure invalidate
the measurement. Completion attribution, not operation start or
physical presentation; a call crossing a boundary belongs to the
completion bin. Retain only complete bins inside guest play/stop
timestamps. Require coverage and conservation against lifetime logs.
Producer bins distinguish original fill outcomes and send outcomes;
view bins distinguish existing SetBitmap outcomes; deferred bins
record handler completion. No scheduler, decoding or rendering
policy changed. Native build and marker-off/on tests still required;
do not run capacity campaign until native conservation passes.
