/*
 * Copyright 2008-2010 Stephan Aßmus <superstippi@gmx.de>
 * All rights reserved. Distributed under the terms of the MIT licensce.
 */


#include "ProxyVideoSupplier.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include <Autolock.h>

#include "VideoTrackSupplier.h"


ProxyVideoSupplier::ProxyVideoSupplier()
	:
	fSupplierLock("video supplier lock"),
	fSupplier(NULL),
	fLabCatchup(access("/boot/home/config/settings/haiku-lab-media-catchup",
		F_OK) == 0),
	fLabCatchupReported(false)
{
}


ProxyVideoSupplier::~ProxyVideoSupplier()
{
}


const media_format&
ProxyVideoSupplier::Format() const
{
	return fSupplier->Format();
}


status_t
ProxyVideoSupplier::FillBuffer(int64 startFrame, void* buffer,
	const media_raw_video_format& format, bool forceGeneration,
	bool& wasCached)
{
	bigtime_t now = system_time();

	BAutolock _(fSupplierLock);
//printf("ProxyVideoSupplier::FillBuffer(%lld)\n", startFrame);
	if (fSupplier == NULL)
		return B_NO_INIT;

	if (fSupplier->CurrentFrame() == startFrame + 1) {
		wasCached = true;
		return B_OK;
	}

	wasCached = false;
	status_t ret = B_OK;
	bigtime_t performanceTime = 0;
	if (fSupplier->CurrentFrame() != startFrame) {
		int64 frame = startFrame;
		ret = fSupplier->SeekToFrame(&frame);
		if (ret != B_OK)
			return ret;
		// Read frames until we reach the frame before the one we want to read.
		// But don't do it for more than 5 frames, or we will take too much
		// time. Doing it this way will still catch up to the next keyframe
		// eventually (we may return the wrong frames until the next keyframe).
		if (!forceGeneration && startFrame - frame > 5) {
			// Lab-only: make bounded forward decoder progress instead of
			// repeatedly abandoning the same keyframe gap. Never submit
			// these intermediate frames. Keep the original timeout
			// result and the existing forced-generation path unchanged.
			if (fLabCatchup && frame >= 0
				&& fSupplier->CurrentFrame() == frame) {
				const bigtime_t recoveryStart = system_time();
				for (int32 i = 0; i < 5; i++) {
					if (i > 0 && system_time() - recoveryStart >= 4000)
						break;
					const int64 before = fSupplier->CurrentFrame();
					if (before >= startFrame)
						break;
					bool intermediateCached = false;
					status_t error = fSupplier->ReadFrame(buffer,
						&performanceTime, format, intermediateCached);
					const int64 after = fSupplier->CurrentFrame();
					if (error != B_OK || after <= before
						|| after > startFrame)
						break;
					if (!fLabCatchupReported) {
						fprintf(stderr, "\nLAB_MEDIA_CATCHUP progress "
							"from=%" B_PRId64 " to=%" B_PRId64 "\n",
							before, after);
						fLabCatchupReported = true;
					}
				}
			}
			return B_TIMED_OUT;
		}
		while (frame < startFrame) {
			ret = fSupplier->ReadFrame(buffer, &performanceTime, format,
				wasCached);
			if (ret != B_OK)
				return ret;
			frame++;
		}
	}

	ret = fSupplier->ReadFrame(buffer, &performanceTime, format, wasCached);

	fProcessingLatency = system_time() - now;

	return ret;
}


void
ProxyVideoSupplier::DeleteCaches()
{
}


void
ProxyVideoSupplier::SetSupplier(VideoTrackSupplier* supplier)
{
	BAutolock _(fSupplierLock);

	fSupplier = supplier;
}

