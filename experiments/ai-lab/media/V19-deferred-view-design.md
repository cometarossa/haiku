# V19 candidate: bounded latest-frame notification

## Evidence and scope
V18 measured 85--91% of SetBitmap time in looper acquisition at
4 HD and 51--53% at 8 HD; draw submission reaches 31--32%.
Persistent BMessenger still fails at 16 SD (30/144 successes).
The separate 8 SD listport campaign observed no full ports in
10 snapshots, but is too sparse to rule out transient backpressure.
Do not increase queue capacities or change BLooper/kernel semantics.

## Candidate
Experiment only, opt-in and software playback initially.
Keep VideoTarget::SetBitmap as the publication point. It already
protects the current bitmap with its own lock, and VideoConsumer
retains the current owned buffer until replacement or unsetting.
A notification contains no bitmap pointer or buffer ownership.
The window looper handles the notification and draws the current
bitmap under the existing bitmap lock. At most one notification
is pending, plus an executing handler. Coalesce intermediate frames;
never queue individual buffer pointers. Clear pending before reading
the current bitmap so publication concurrent with drawing can
request another notification.

Use bounded nonblocking notification submission. Failed enqueue
must release the pending reservation and fall back to existing
synchronous submission for that call, rather than silently lose
the final update. Review local BMessenger delivery path and cached
target lifetime before implementing. Null publication continues
to skip window acquisition; a stale queued notification must see
the current null and do nothing. Never recycle a buffer while the
existing bitmap lock protects a drawing operation.

## Necessary design gates
- Preserve default behavior when marker absent.
- Prove target attach/detach and MainWin destruction ordering.
- No unlocked reads of overlay/subtitle state; do not route overlay
  transitions, subtitles or unsupported view state through the
  experiment until their semantics are proved.
- Handle stop, seek, resize, window hide, display mode changes,
  and failed message delivery. Existing Draw() repaint semantics
  remain available; direct drawing must not use stale frame pointers.
- Keep counters for publication, notification reservation, coalescing,
  delivery failure, handler invocation and actual submission.
  A submission is not physical presentation.
- Native smoke: correct dynamic frame, stop/seek/resume, close/reopen,
  no deadlock, no stale frame after stop, no marker leakage.
- Matched OFF/ON/ON/OFF with fixed duration and balanced load:
  4/8 SD and HD, then 16 SD. Persistent query timings plus visual
  frame advancement/correctness. A win requires responsiveness
  without an unacceptable loss of displayed updates.

The initial state-machine model is deliberately isolated from
production VideoView. It tests the notification reservation rule,
not Haiku's message ordering or bitmap lifetime. It must not be
treated as a working renderer or proof of thread safety.

## First integration
LabDeferredVideo.h uses a one-way attachment/ready/pending/disabled
atomic state. Cached BMessenger is initialized on attachment before
controller target publication; no queued pointer payload. Any overlay
bitmap or subtitle update permanently disables the experiment for that
view, as does detachment. The fallback remains the original path.
Null publication leaves an already pending message harmless: handler
reads current bitmap only under the existing bitmap lock. A message
already executing can finish drawing the previous valid bitmap while
publication waits for that lock. No stronger display completion or
stop guarantee than the existing async server path is claimed.

Local BMessage::_SendMessage may enqueue directly in BDirectMessageTarget
rather than the IPC port; the observed low port occupancy does not
measure this internal queue. The timeout of zero applies to port
fallback, not internal token/queue lock scheduling. A local send may
return success during target closure; lifetime teardown must be
validated, and the state is never revived after detach.
V19 view stats append deferred publication count; a separate record
tracks queue reservations, coalesces, failures, handlers, cancelled
messages and draws. Host test compiles the actual helper with mock
atomic and messenger primitives; no native concurrency proof yet.

## V20 timing follow-up
The first 16-stream pair shows a new bottleneck: ON 4838 of 6378
publications coalesced, only 1536 draw requests versus 3291 OFF;
both playback validations fail. Add independently gated
haiku-lab-video-deferred-timing diagnostics to measure time from
notification reservation to handler start, elapsed handler time,
bitmap lock acquisition and draw submission. Queue time includes
sender overhead and scheduling; handler duration includes unlock
and bookkeeping outside measured phases. No CPU or display FPS
claim. Timestamp is stored before submission, read before releasing
pending. No behavioral treatment change; marker OFF avoids clocks.
ProxyVideoSupplier::FillBuffer explicitly returns B_TIMED_OUT when
a non-forced requested frame is more than five frames ahead after
SeekToFrame; this is distinct from fManager lock timeout. Seek and
ReadFrame can also propagate errors. Need categorize these causes
before changing the decoder recovery policy. Do not assume every
fill timeout is a lock timeout. Existing V19 build remains active.
