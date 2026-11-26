# V21 frame-gap distribution across tracks
Derived from validated V21 isolated thread-policy campaigns (4/8/16
streams) and original per-track LAB_VIDEO_PROXY lifetime records.
Denominator: calls with an available track, not producer fills.
JSON contains sorted fractions, not identities; record ordering
does not establish correspondence to windows or other log records.

At four streams no track records a frame-gap timeout. At eight,
the four trials have respectively 2, 3, 0, 7 affected tracks.
At sixteen, all sixteen tracks are affected in all four trials.
Even the least affected track in each sixteen-stream trial has
a gap timeout fraction above 42%. This is broad saturation rather
than just a few starved streams. Single-thread treatment helps
but does not remove the broad failure. A few repeated trials on
a non-isolated host cannot establish scheduler causation.
Before changing recovery, complete the combined treatment;
then consider a separate keyframe-interval experiment holding
codec, resolution, content, thread policy and renderer fixed.
Measure actual decoded/presented progress separately from requests.
No production change here.
