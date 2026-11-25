# Graphics backpressure: source audit after V16
Source revision f960376e (unchanged graphics paths in V16).
The 8-HD ON trials failed control responsiveness; 16-SD OFF/ON
first pair also invalid. More successful FillBuffer calls are not
sufficient for responsiveness.

Observed source chain:
- VideoConsumer::_HandleBuffer holds fTargetLock around SetBitmap;
  it retains the latest shared bitmap buffer until replacement.
- VideoView::SetBitmap calls VideoTarget::SetBitmap (ordinary
  blocking BLocker), then attempts LockLooperWithTimeout(10000).
  The 10 ms timeout only covers acquisition, not the work after it.
- While holding the looper and bitmap locks, the direct drawing
  branch calls _DrawBitmap -> BView::DrawBitmapAsync.
- BView::DrawBitmapAsync queues AS_VIEW_DRAW_BITMAP and calls
  _FlushIfNotInTransaction -> BWindow::Flush -> ServerLink::Flush.
- LinkSender::Flush defaults to B_INFINITE_TIMEOUT and uses write_port.
  The receiving ServerWindow message port has capacity 100.
  Thus the asynchronous call does not guarantee bounded submission.
- ServerWindow handles AS_VIEW_DRAW_BITMAP with DrawingEngine::DrawBitmap.
  Its WaitForRetrace call is commented out; deleting B_WAIT_FOR_RETRACE
  at the MediaPlayer call site is not an evidence-backed fix.
- Existing V15 target-call time includes the complete SetBitmap call
  (including waits), and counts attempts, not successful draws or
  physical presentation. HD ON total target times were much higher,
  but durations differed.

Hypothesis: increased decoded output may congest software drawing or
IPC and hold window locks, delaying the scripting interface. Other
lock contention and host scheduling are possible; no port saturation
has yet been observed directly.

Next experiment (after V17 validation): opt-in counters at VideoView
for bitmap update, looper acquisition (success/timeout), bitmap lock,
draw-submission duration, subtitle invalidation and overlay paths.
Capture separately: window responsiveness, accepted draw requests,
app_server bitmap handling time and bounded queue occupancy samples.
Use one terminal summary per view, not per-frame logs, with explicit
lifetime boundaries and independent synchronization review.
Compare 4/8 SD and HD before modifying IPC policy. Never silently
discard arbitrary port messages, shorten a generic Flush timeout,
recycle a still-referenced bitmap, or change retrace globally.
A future frame-coalescing protocol must prove buffer ownership and
ordering, preserve seek/stop and overlay semantics, and pass pixel
correctness tests. No behavior change in this audit.
