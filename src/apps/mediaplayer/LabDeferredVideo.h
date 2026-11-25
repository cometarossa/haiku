/* Experimental opt-in latest-frame notification. MIT license. */
#ifndef LAB_DEFERRED_VIDEO_H
#define LAB_DEFERRED_VIDEO_H

#include <Message.h>
#include <Messenger.h>
#include <OS.h>
#include <stdio.h>
#include <unistd.h>


class LabDeferredVideo {
public:
	LabDeferredVideo()
		:
		fRequested(access("/boot/home/config/settings/haiku-lab-video-deferred",
			F_OK) == 0),
		fTiming(fRequested && access(
			"/boot/home/config/settings/haiku-lab-video-deferred-timing",
			F_OK) == 0),
		fState(fRequested ? kUnattached : kDisabled),
		fQueued(0), fCoalesced(0), fFailed(0), fHandled(0),
		fCancelled(0), fDraw(0), fSkipped(0), fEnqueueTime(0),
		fQueueUs(0), fHandlerUs(0), fBitmapUs(0), fDrawUs(0)
	{
	}

	// Called once on initial attachment, before the controller publishes
	// the target. The messenger is immutable afterwards.
	void Attach(BHandler* handler)
	{
		if (!fRequested || atomic_get(&fState) != kUnattached)
			return;
		if (fMessenger.SetTo(handler) == B_OK)
			atomic_test_and_set(&fState, kReady, kUnattached);
		else
			Disable();
	}

	bool Enabled()
	{
		if (!fRequested)
			return false;
		int32 state = atomic_get(&fState);
		return state == kReady || state == kPending;
	}

	// Sticky for this view lifetime: never revive a queued old message.
	void Disable()
	{
		if (fRequested)
			atomic_set(&fState, kDisabled);
	}

	// Consumer publication is serialized by its existing target lock.
	// Local SendMessage may take internal queue/token locks; zero timeout
	// bounds the port fallback, not all internal scheduling/locking.
	bool TryQueue(uint32 what)
	{
		if (!fRequested)
			return false;
		int32 previous = atomic_test_and_set(&fState, kPending, kReady);
		if (previous == kPending) {
			atomic_add64(&fCoalesced, 1);
			return true;
		}
		if (previous != kReady)
			return false;
		if (fTiming)
			atomic_set64(&fEnqueueTime, system_time());
		BMessage message(what);
		if (fMessenger.SendMessage(&message, BMessenger(), 0) == B_OK) {
			atomic_add64(&fQueued, 1);
			return true;
		}
		atomic_test_and_set(&fState, kReady, kPending);
		atomic_add64(&fFailed, 1);
		return false;
	}

	bool BeginHandle()
	{
		if (!fRequested)
			return false;
		// Read the timestamp before clearing the reservation; a new
		// publication may replace it as soon as the state is ready.
		const int64 enqueue = fTiming ? atomic_get64(&fEnqueueTime) : 0;
		const bigtime_t now = Now();
		// Release reservation before acquiring bitmap lock.
		if (atomic_test_and_set(&fState, kReady, kPending) != kPending) {
			atomic_add64(&fCancelled, 1);
			return false;
		}
		atomic_add64(&fHandled, 1);
		if (fTiming)
			atomic_add64(&fQueueUs, now - enqueue);
		return true;
	}

	bigtime_t Now() const
	{
		return fTiming ? system_time() : 0;
	}

	void FinishHandle(bool drew, bigtime_t elapsed = 0,
		bigtime_t bitmap = 0, bigtime_t draw = 0)
	{
		atomic_add64(drew ? &fDraw : &fSkipped, 1);
		if (fTiming) {
			atomic_add64(&fHandlerUs, elapsed);
			atomic_add64(&fBitmapUs, bitmap);
			atomic_add64(&fDrawUs, draw);
		}
	}

	void Report()
	{
		if (!fRequested)
			return;
		fprintf(stderr, "\nLAB_VIDEO_DEFERRED queued=%" B_PRId64
			" coalesced=%" B_PRId64 " failed=%" B_PRId64
			" handled=%" B_PRId64 " cancelled=%" B_PRId64
			" draw=%" B_PRId64 " skipped=%" B_PRId64 "\n",
			atomic_get64(&fQueued), atomic_get64(&fCoalesced),
			atomic_get64(&fFailed), atomic_get64(&fHandled),
			atomic_get64(&fCancelled), atomic_get64(&fDraw),
			atomic_get64(&fSkipped));
		if (fTiming) {
			fprintf(stderr, "\nLAB_VIDEO_DEFERRED_TIMING queue_us=%" B_PRId64
				" handler_us=%" B_PRId64 " bitmap_us=%" B_PRId64
				" draw_us=%" B_PRId64 "\n",
				atomic_get64(&fQueueUs), atomic_get64(&fHandlerUs),
				atomic_get64(&fBitmapUs), atomic_get64(&fDrawUs));
		}
	}

private:
	enum { kUnattached = -1, kDisabled, kReady, kPending };
	const bool fRequested;
	const bool fTiming;
	int32 fState;
	BMessenger fMessenger;
	int64 fQueued, fCoalesced, fFailed, fHandled, fCancelled, fDraw, fSkipped;
	int64 fEnqueueTime, fQueueUs, fHandlerUs, fBitmapUs, fDrawUs;
};

#endif
