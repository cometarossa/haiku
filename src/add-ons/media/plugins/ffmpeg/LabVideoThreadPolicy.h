/* Experimental bounded decoder parallelism. MIT license. */
#ifndef LAB_VIDEO_THREAD_POLICY_H
#define LAB_VIDEO_THREAD_POLICY_H

// Restrict experiment to known small H.264 video. Keep all other
// codecs, audio, unknown dimensions and larger frames unchanged.
inline int
LabVideoThreadCount(int original, bool enabled, bool h264, int width,
	int height)
{
	if (enabled && h264 && original > 1 && width > 0 && height > 0
		&& width <= 640 && height <= 480)
		return 1;
	return original;
}

#endif
