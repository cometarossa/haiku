# V18 persistent query capacity test
V18 fb8c2e41, 120 s numbered SD fixture, probe d9c8b5b9.
All diagnostics ON, speculative recovery OFF. One staged run per
4/8/16 windows. 4 and 8 pass all queries and playback advancement;
16 fails (30 successes, 6 errors, 108 unattempted of 144).
The 15 s budget returned after 15.001259 s. All player exits zero,
RAMFS unmounted and final marker received. Native view records
4/8/16; no FPS or steady-state performance claim. Sampling duration
and method differ from prior hey campaigns; not a matched comparison.
Three stable QEMU processes, host not isolated. Full screenshots
remain on host. Next: dedicated queue sampling under load.
