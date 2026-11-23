# Haiku R1/beta6 app_server window lifecycle baseline

AI-assisted independent research fork; not official Haiku testing.

The unmodified Haiku R1/beta6 x86_64 guest, running under an isolated
QEMU/HVF overlay on macOS, compiled and executed
experiments/ai-lab/desktop/window_lifecycle.cpp using native g++ and
the Be interface library:

    g++ -std=c++11 -O2 -Wall -Wextra -o window_lifecycle windows.cpp -lbe

The test uses a real BApplication and concurrently visible BWindow
loopers to create and close windows in batches.

- 5 batches x 8 windows = 40 successful lifecycles, 0 failures.
- 20 batches x 10 windows = 200 successful lifecycles, 0 failures.
- Total: 240 create/show/lock/quit lifecycles with zero reported errors.

CSV and stderr files were transferred directly from the Haiku guest
and are checked by desktop/test_evidence.py. A QEMU HMP screenshot of
the successful 200-window run is included, along with SHA256 checksums.

Limitations: virtualization means results do not measure bare-metal
windowing speed, app_server input-to-photon latency or GPU performance.
Success on this one fixture and virtual hardware is not proof of
app_server correctness in all conditions. No Haiku fork-built image
has been booted yet to compare these results.
