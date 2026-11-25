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
