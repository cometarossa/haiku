# V10 first independent local build and native profile smoke
AI-assisted independent research fork. ZimaBlade Linux builder,
Ubuntu24-v2, 2 CPUs, 4 GiB cap, source 12b5c9ec, official buildtools
33d46bf5. Build completed exit 0, no OOM, 2026-11-25 10:52:44 UTC
to 13:19:09 UTC. Jam updated 17100 targets. 650 MiB raw image,
459 MiB compressed. Logs retained on Zima and Sequoia staging.
Both SHA256 hashes verified on Mac. Local import and independent
QEMU/HVF overlay, 4 vCPU/8 GiB, localhost VNC 5914, GUI and Terminal
verified. No CI dependency. Same fixed-work binary hash as prior
V9 control. 12 runs, 36 worker rows, 49152 fills, 2359296 final RGB
checks, zero errors. Profile on: 18 complete per-window records,
24576 AS_FILL_RECT dispatches; off: zero records. All normal deletion.
Two OFF and two ON runs per topology, batch64 only. Marker removed
by successful guest scripts. Acquisition measurements include scheduling;
dispatch subsets overlap dispatch total. Summed window times are not
elapsed client time. Uncontrolled host load, high timing variability,
not enough repetitions for overhead or causality claims.
No additional OS modifications in this evidence commit.
Remaining: full paired acceptance (batch1/64/1024, more repeats),
V8 IPC and memory validation, onscreen/Media Kit regression.
