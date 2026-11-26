# V23 MediaPlayer app_server profiling
The existing offscreen fixed-work profiler is deliberately left intact.
New marker: /boot/home/config/settings/haiku-lab-media-appserver-profile.
Only non-offscreen windows of the exact MediaPlayer signature qualify;
auxiliary windows may also appear. No new lock or scheduling policy.
Reuse per-looper elapsed timing for window, desktop read/write lock
acquisition, dispatch, sync, fill, bitmap; add redraw and outer batch
elapsed times. Bitmap dispatch includes clipping and drawing engine
work, and may return early. It is not presented frames or pure raster
time. Redraw and batch are overlapping phases; do not sum all phases.
Report once at looper exit outside locks to serial, separate prefix
LAB_MEDIA_APPWIN. Include normal-delete marker. No per-frame logging.
All records are lifetime diagnostics, not observation-window measures;
compare separately with V22 observation counters and actual teardown.
Native validation required, including marker-off serial absence,
normal completion and coverage of bitmap-active windows. Do not
equate all windows to video tracks without identifying auxiliary ones.
No performance claim; subsequent finer profiling may separate
clipping, parallel lock acquisition, pixel path and server draw.
