# V15 host-load comparison
Same V15 db20e3f2 image, same fixture, same guest script except directory name.
4/8 distinct windows, 36/36 true advancing samples per campaign.
Before: 14 QEMUs, after: 3 QEMUs (2 Haiku plus Fincept). Host load
not isolated; order fixed, warm cache and variable playback startup
and stop durations confound results. Counts span whole node lifetime.
After n8 raw log interleaves a complete producer record after
"VideoProducer: dropped frame (271) (perf. time". Normalized derivative
only separates this record with a newline; raw preserved. All 8+8
records pass conservation; strict raw parser correctly rejects n8.
Do not infer displayed FPS or attribute the entire effect causally.
No VM disks deleted. ACPI shutdown of 11 guests verified separately.
