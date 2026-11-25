/*
 * Experimental diagnostics for the independent Haiku research fork.
 * Distributed under the terms of the MIT license.
 */
#ifndef LAB_VIDEO_VIEW_STATS_H
#define LAB_VIDEO_VIEW_STATS_H

#include <OS.h>
#include <stdio.h>
#include <unistd.h>


// SetBitmap is called under the existing consumer target lock. Keep
// counters atomic across callers; report only after target detachment.
class LabVideoViewStats {
public:
	enum Outcome {
		kNull, kLooperFail, kBitmapFail, kOverlay, kInvalidate, kDraw,
		kOutcomeCount
	};

	LabVideoViewStats()
		:
		enabled(access("/boot/home/config/settings/haiku-lab-video-view-stats",
			F_OK) == 0),
		calls(0), outcomes(), total(0), update(0), looper(0),
		bitmap(0), overlay(0), invalidate(0), draw(0)
	{
	}

	void Report()
	{
		if (!enabled)
			return;
		fprintf(stderr, "\nLAB_VIDEO_VIEW calls=%" B_PRId64
			" null=%" B_PRId64 " looper_fail=%" B_PRId64
			" bitmap_fail=%" B_PRId64 " overlay=%" B_PRId64
			" invalidate=%" B_PRId64 " draw=%" B_PRId64
			" total_us=%" B_PRId64 " update_us=%" B_PRId64
			" looper_us=%" B_PRId64 " bitmap_us=%" B_PRId64
			" overlay_us=%" B_PRId64 " invalidate_us=%" B_PRId64
			" draw_us=%" B_PRId64 "\n",
			atomic_get64(&calls), atomic_get64(&outcomes[kNull]),
			atomic_get64(&outcomes[kLooperFail]),
			atomic_get64(&outcomes[kBitmapFail]),
			atomic_get64(&outcomes[kOverlay]),
			atomic_get64(&outcomes[kInvalidate]),
			atomic_get64(&outcomes[kDraw]), atomic_get64(&total),
			atomic_get64(&update), atomic_get64(&looper),
			atomic_get64(&bitmap), atomic_get64(&overlay),
			atomic_get64(&invalidate), atomic_get64(&draw));
	}

	class Sample {
	public:
		explicit Sample(LabVideoViewStats& stats)
			:
			fStats(stats), start(Now()), outcome(kOutcomeCount),
			update(0), looper(0), bitmap(0), overlay(0),
			invalidate(0), draw(0)
		{
		}

		~Sample()
		{
			if (!fStats.enabled)
				return;
			// An unexpected outcome remains detectable by conservation.
			bigtime_t elapsed = Elapsed(start);
			atomic_add64(&fStats.calls, 1);
			if (outcome < kOutcomeCount)
				atomic_add64(&fStats.outcomes[outcome], 1);
			atomic_add64(&fStats.total, elapsed);
			atomic_add64(&fStats.update, update);
			atomic_add64(&fStats.looper, looper);
			atomic_add64(&fStats.bitmap, bitmap);
			atomic_add64(&fStats.overlay, overlay);
			atomic_add64(&fStats.invalidate, invalidate);
			atomic_add64(&fStats.draw, draw);
		}

		bigtime_t Now() const
		{
			return fStats.enabled ? system_time() : 0;
		}

		bigtime_t Elapsed(bigtime_t since) const
		{
			return fStats.enabled ? system_time() - since : 0;
		}

	private:
		LabVideoViewStats& fStats;
		bigtime_t start;

	public:
		Outcome outcome;
		bigtime_t update, looper, bitmap, overlay, invalidate, draw;
	};

private:
	const bool enabled;
	int64 calls;
	int64 outcomes[kOutcomeCount];
	int64 total, update, looper, bitmap, overlay, invalidate, draw;
};

#endif
