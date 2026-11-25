# V18 VideoView submission diagnostics (not yet a rendering optimization)

Opt-in marker: /boot/home/config/settings/haiku-lab-video-view-stats.
Sample each VideoView::SetBitmap invocation; one summary per view on
destruction. Existing target/looper/bitmap locks and drawing calls
remain in the original order. NULL still bypasses window locking.
Disabled mode does not read the clock or update atomic counters.
Enabled mode adds clock reads and atomic counters; measure overhead.

Outcome conservation: calls = null + looper_fail + bitmap_fail +
overlay + invalidate + draw. Overlay means final overlay-active
branch, not proof that an overlay was successfully presented.
Draw means direct _DrawBitmap returned, not GPU/display completion.
Time buckets are disjoint: target update, looper acquisition,
bitmap acquisition, overlay handling/checks, invalidation or direct
draw submission. total_us includes unlocks and uninstrumented gaps.
The ordinary Draw() repaint path is intentionally excluded.

Lifetime review: consumer calls SetBitmap under fTargetLock;
MainWin::~MainWin detaches via Controller::SetVideoTarget(NULL)
before deleting views and waits for the controller thread. Counters
use Haiku atomic primitives, but still require this existing lifetime
contract; no asynchronous new pointer ownership or thread created.
No arbitrary message drops, IPC deadline changes, bitmap recycling,
or global rendering policy changes.

Host test compiles the actual SetBitmap body with fake view/clock
and tests all six terminal outcomes, timing conservation, lock balance,
and disabled clock reads. Native testing still required, including
marker isolation, teardown, actual software and overlay paths.
Compare 4/8 streams SD/HD with same-image stats OFF/ON; correlate
SetBitmap durations with scripting latency. High draw time alone
does not prove port saturation; separate app_server timing/queue
occupancy experiment required.
