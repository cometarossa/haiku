# V20 four-stream diagnostic gate
Image 11904750; 120s SD fixture, OFF/ON/ON/OFF. All four
trials pass both diagnostic and playback checks. Proxy lifetime
records and producer fill timeout counts agree (zero throughout).
ON 5354 draw submissions, 6 coalesces; OFF 5062 draws.
ON queue time 9094900 us / 5354 handlers = 1698.7 us/handler.
ON handler time 200779 us / 5354 handlers = 37.5 us/handler.
Queue time includes publication/send overhead and scheduling.
Handler time is elapsed, not CPU time or physical display latency.
Counters span node lifetimes; no FPS or whole-system speedup claim.
Three QEMU PIDs stable, host not isolated. Gate for larger loads met.
