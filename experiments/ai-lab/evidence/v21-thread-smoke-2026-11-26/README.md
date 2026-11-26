# V21 single-window lifecycle smoke
Image 2f9d27bf; thread treatment OFF/ON, deferred rendering OFF.
Verified stop at zero, seek to preceding keyframe 28s, resume,
pause holds position, all 18 BMessenger requests succeed.
FFmpeg reports effective 4 vs 1 thread; both player exits zero.
Draw submissions 146/148, one looper timeout per lifetime.
Native cleanup confirmed. No speed or physical FPS inference.
