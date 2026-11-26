/* Opt-in time-binned video diagnostics. MIT license. */
#ifndef LAB_OBSERVATION_STATS_H
#define LAB_OBSERVATION_STATS_H

#include <OS.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

// Completion events in absolute monotonic one-second bins. No per-event
// file access or logging, no new locks. Never overwrite an old bin.
// Report only after the caller's existing lifetime synchronization.
class LabObservationStats {
public:
	enum { kBins = 512, kKinds = 8 };
	explicit LabObservationStats(bool enabled)
		:
		fRequested(enabled && access(
			"/boot/home/config/settings/haiku-lab-video-observation", F_OK) == 0),
		fCreated(fRequested ? system_time() : 0),
		fAnchor(fCreated / 1000000 * 1000000),
		fCounts(fRequested ? static_cast<int64*>(calloc(kBins * kKinds,
			sizeof(int64))) : NULL),
		fOverflow(0)
	{
	}

	~LabObservationStats()
	{
		free(fCounts);
	}

	void Record(int kind, bigtime_t now)
	{
		if (!fCounts)
			return;
		if (now < fCreated || now - fAnchor >= (bigtime_t)kBins * 1000000
			|| kind < 0 || kind >= kKinds) {
			atomic_add64(&fOverflow, 1);
			return;
		}
		atomic_add64(&fCounts[(now - fAnchor) / 1000000 * kKinds + kind], 1);
	}

	void Record(int kind)
	{
		if (fCounts)
			Record(kind, system_time());
	}

	void Report(const char* stage, int64 id)
	{
		if (!fRequested)
			return;
		fprintf(stderr, "\nLAB_OBSERVATION stage=%s id=%" B_PRId64
			" anchor=%" B_PRId64 " created=%" B_PRId64
			" ended=%" B_PRId64 " overflow=%" B_PRId64 " valid=%d\n",
			stage, id, fAnchor, fCreated, system_time(),
			atomic_get64(&fOverflow), fCounts != NULL ? 1 : 0);
		if (!fCounts)
			return;
		for (int i = 0; i < kBins; ++i) {
			int64 c[kKinds];
			bool nonzero = false;
			for (int k = 0; k < kKinds; ++k) {
				c[k] = atomic_get64(&fCounts[i * kKinds + k]);
				nonzero |= c[k] != 0;
			}
			if (!nonzero)
				continue;
			fprintf(stderr, "\nLAB_OBSERVATION_BIN stage=%s id=%" B_PRId64
				" bin=%" B_PRId64 " c0=%" B_PRId64 " c1=%" B_PRId64
				" c2=%" B_PRId64 " c3=%" B_PRId64 " c4=%" B_PRId64
				" c5=%" B_PRId64 " c6=%" B_PRId64 " c7=%" B_PRId64 "\n",
				stage, id, fAnchor + (bigtime_t)i * 1000000,
				c[0], c[1], c[2], c[3], c[4], c[5], c[6], c[7]);
		}
	}

private:
	LabObservationStats(const LabObservationStats&);
	LabObservationStats& operator=(const LabObservationStats&);
	const bool fRequested;
	const bigtime_t fCreated, fAnchor;
	int64* const fCounts;
	int64 fOverflow;
};

#endif
