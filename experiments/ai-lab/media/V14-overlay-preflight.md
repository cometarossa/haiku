# V14 candidate: MediaPlayer overlay capability preflight
V13 screeninfo confirms Generic VESA and no supported overlay spaces.
With the lab marker haiku-lab-media-overlay-preflight present, only
MediaPlayer's initial connection changes: for a concrete supported
bitmap color space lacking the overlay flag, use software directly;
choose RGB32 if BViews cannot draw the requested format. Wildcard,
unsupported and overlay-capable spaces retain prior negotiation.
Existing connection retry remains unchanged. Marker absent by default.
The public capability API can report no support on IPC failure; this
conservative software path is therefore not proof of hardware absence.
Native compilation and validation pending. Require same-image marker
OFF/ON, identical fixtures, successful playback and pixel checks,
startup timing with repeated samples, no new crashes. Hardware capable
overlay and audio tests remain separate. Do not claim playback FPS
improvement merely from avoiding a failed connection.
