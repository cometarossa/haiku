# Empty-port deadline timing baseline on V4
AI-assisted independent research fork. V4 ai_35eca30c. Native binary
compiled on beta6 and hash-verified on V4. The sleeping observer uses
priorities 10/15/100/110, zero/two bounded normal-priority workers,
and absolute empty-port read timeouts on a 10ms grid. No advance vs
one initial API estimate as advance (100us in every trial).
80 samples per condition, 1280 total; all trials completed.
Signed error = actual return time minus nominal event time.
This models a portion of Media Kit wake-ahead behavior, not actual
Media Kit graph execution, audio buffer delivery, or video playback.
Single run per condition; no host load control. No causal or hardware
performance claim. Repeat with the identical binary on V5.
