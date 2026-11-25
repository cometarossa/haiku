# V16 16-stream capacity experiment
320x180 H.264, 30 fps, 20 s numbered clip; 16 independent windows.
Four OFF/ON/ON/OFF trials, 3 stable QEMU PIDs. All guest process
exits zero and final marker received after RAMFS cleanup. Strict
validation is separate from process completion; results include invalid
trials. Short clip and sequential scripting can end playback before
sampling completes. Do not infer displayed FPS or a stable 16-stream
capacity. Preserve negative evidence and repeat with longer clip and
per-query timings. Raw screenshot sequence remains on host.
