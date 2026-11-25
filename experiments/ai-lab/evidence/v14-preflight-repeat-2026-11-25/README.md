# V14 balanced native preflight startup proxy
12 completed launches, six balanced OFF/ON pairs on 63cc5489-trial1.
Every OFF run retries without overlay; every ON run preflights and
avoids that retry. All processes exit zero. Paired median ON/OFF
startup proxy ratio .5392, range .5131.. .7406, six of six wins.
Proxy is monotonic guest launch to first positive controller position
with IsPlaying=true; polling and scripting costs included. Not first
pixel, not physical display latency. No producer drop messages in
these short single-player samples; five buffer-send errors per
treatment in final logs, none visible in prequit snapshots. stdout
buffering means timing of the errors remains unknown. Host not
isolated, identical small synthetic fixture, no audio. Keep opt-in.
