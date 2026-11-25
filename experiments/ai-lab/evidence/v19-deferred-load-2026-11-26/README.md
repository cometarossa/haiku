# V19 same-image balanced 4/8 SD comparison
Image 067ee57e. All eight trials validate (playback, queries,
activation, cleanup and 20--22 s observation). Diagnostics enabled
in both treatments, no speculative decoder recovery. V19 ON is
NOT accepted as a performance win: at 4 streams, 5347 vs 5205
draw submissions and 29 vs 73 late consumer buffers, but at 8,
6345 vs 8057 draws and 3173/10633 vs 1517/11558 fill timeouts.
8-stream Position p95 OFF 19.896/106.031 ms and ON 32.751/246.017 ms.
Producer-side SetBitmap elapsed excludes deferred rendering work.
Counters cover whole lifetimes, not physical presentation or fixed
observation alone. Host load not isolated, two pairs only.
Keep default OFF. 16-stream diagnostic comparison may characterize
capacity, not promote the treatment. Investigate window dispatch
cost and decoder contention before further production changes.
