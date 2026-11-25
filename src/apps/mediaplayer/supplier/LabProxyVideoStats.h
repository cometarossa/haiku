/* Experimental decoder diagnostics. MIT license. */
#ifndef LAB_PROXY_VIDEO_STATS_H
#define LAB_PROXY_VIDEO_STATS_H

#include <OS.h>
#include <stdio.h>
#include <unistd.h>

// Access only while holding ProxyVideoSupplier's existing supplier lock.
// Report/reset at track replacement, not process destruction.
class LabProxyVideoStats {
public:
	LabProxyVideoStats()
		:
		enabled(access("/boot/home/config/settings/haiku-lab-video-proxy-stats",
			F_OK) == 0), calls(0), cached(0), gapTimeout(0), seekTimeout(0),
		readTimeout(0), otherErrors(0), success(0), gapFrames(0), maxGap(0)
	{
	}

	status_t Finish(status_t result, bool seek = false)
	{
		if (enabled) {
			if (result == B_OK)
				++success;
			else if (result == B_TIMED_OUT) {
				if (seek)
					++seekTimeout;
				else
					++readTimeout;
			} else
				++otherErrors;
		}
		return result;
	}

	void Gap(int64 frames)
	{
		if (enabled) {
			++gapTimeout;
			gapFrames += frames;
			if (frames > maxGap)
				maxGap = frames;
		}
	}

	void ReportAndReset()
	{
		if (!enabled)
			return;
		fprintf(stderr, "\nLAB_VIDEO_PROXY calls=%" B_PRId64
			" cached=%" B_PRId64 " gap_timeout=%" B_PRId64
			" seek_timeout=%" B_PRId64 " read_timeout=%" B_PRId64
			" other_errors=%" B_PRId64 " success=%" B_PRId64
			" gap_frames=%" B_PRId64 " max_gap=%" B_PRId64 "\n",
			calls, cached, gapTimeout, seekTimeout, readTimeout,
			otherErrors, success, gapFrames, maxGap);
		calls = cached = gapTimeout = seekTimeout = readTimeout = 0;
		otherErrors = success = gapFrames = maxGap = 0;
	}

	const bool enabled;
	int64 calls, cached, gapTimeout, seekTimeout, readTimeout;
	int64 otherErrors, success, gapFrames, maxGap;
};

#endif
