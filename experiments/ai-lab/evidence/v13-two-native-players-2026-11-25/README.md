# V13 simultaneous MediaPlayer controller playback
Two independent native windows (indices 3 and 5) identified by title.
Native hey scripting sets distinct frames, stops and starts both.
Four samples show both IsPlaying=true and increasing positions.
Screenshots show both visible windows; dynamic stream A frame index
64 then 143; stream B is a color-bar fixture, not suitable for visual
frame-change counting. Both playback sliders advance. The initial
scripting attempt using -o cannot print B_INT64_TYPE or B_RECT_TYPE;
normal hey message output works. Position is controller time, not
a count of presented frames. No audio or dropped-frame claim.
