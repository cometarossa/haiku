# V22 producer timing audit

Derived JSON covers all 24 diagnostic-valid V21 thread and combined
trials. The original producer measures elapsed FillBuffer and buffer
acquisition (WaitForBuffers plus RequestBuffer), not thread CPU time.
The consumer measures elapsed target calls; with deferred rendering,
these mostly publish rather than draw. All counters span lifetimes.

At sixteen streams with one thread and synchronous rendering,
mean fill time is only 0.276--0.330 ms across the four trials,
despite frame-gap timeout rates of 56--73%. Successful decodes and
early gap rejections share the same denominator; this does not show
that decoding itself is inexpensive or that lowering fill time helps.
The consumer target mean is 18.85--21.18 ms in these four trials.
The buffer wait mean falls from about 32 ms at four streams to
5.55--8.62 ms at sixteen. This includes natural pacing and recycled
buffers after rejected fills; not an isolated measure of contention.

VideoProducer recycles the buffer on timeout and increments fFrame;
the displayed last valid frame is held. It does not reschedule the
same target. ProxyVideoSupplier seeks then rejects a remaining gap
above five on non-forced requests. This can sustain a recovery gap
until the next keyframe. Do not freeze the media clock or alter the
forced-generation path to reduce timeout counts.

Candidate next instrumentation, if GOP sensitivity warrants a new
build: separate successful, cached, gap-rejected and other fill
elapsed times; account for seek and actual frame reads, with
conservation and an independent opt-in marker. Preserve existing
clock semantics and default behavior. No source changes in this audit.
