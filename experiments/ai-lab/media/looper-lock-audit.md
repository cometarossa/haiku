# BLooper timeout fast-path audit (V18)
Four-HD VideoView ON records attribute 85.09% and 91.04% of
SetBitmap time to the looper acquisition phase. These are cumulative
elapsed times, not CPU times or a direct measure of the lock holder.

BLooper::_Lock holds the global gLooperList lock before incrementing
fAtomicCount and invoking _LockComplete. A timed-out acquire_sem_etc
does not undo that increment. Unlock decrements once and releases the
semaphore if the previous count exceeds one. Consequently a timeout
may leave the idle count positive and permanently route later
acquisitions through the semaphore. BLocker::AcquireLock explicitly
documents this tradeoff and the race that would be created by naively
decrementing on timeout; existing BLocker tests reflect BeOS behavior.
CountLockRequests is therefore not a reliable live waiter count.

Do not change the counter algorithm on the basis of this observation.
The looper timing also includes the global registry lock and scheduling,
and a large time share does not establish this fallback as the cause.

looper_lock_probe.cpp compares two fresh, non-running BLoopers, one
with a deliberately induced timeout on a worker while the main thread
holds the lock. Then both are measured in alternating order for six
50k-iteration uncontended lock/unlock batches, with count checks.
Run outside the media campaign. Record release build provenance,
timings and retained counts. This isolates fallback cost, not actual
contended MediaPlayer latency. No production code change.
