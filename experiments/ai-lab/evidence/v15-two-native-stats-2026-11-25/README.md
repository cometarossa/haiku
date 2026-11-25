# V15 two-window stats
Source db20e3f2. Same hashed 320x180 moving fixture, both markers ON.
Two distinct windows, 6/6 active controller states and advancing positions.
486 sends, 478 target calls, 0 late at each stage, 0 send errors,
0 consumer copy bytes. Explicit stop before quit; no causal conclusion
from one run. Counts span startup/stop, no displayed FPS claim.
Subsequent 4-window automation did not complete: 400 ms open interval
conflicted with MainApp::RefsReceived 500 ms playlist coalescing.
No 4/8-window performance evidence from this attempt.
