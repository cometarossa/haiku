# V21 candidate: decoder parallelism budget

V20 eight-stream runs attribute every producer fill timeout to the
explicit >5-frame gap policy, not a propagated seek/read timeout.
First 16-stream OFF run: 13424/21123 gap timeouts, max gap 119 frames.
This measures distance, not the root cause of falling behind.

AVCodecDecoder::NegotiateOutputFormat currently sets thread_count
to system_info.cpu_count for EVERY codec context. In the four-vCPU
guest, 16 H.264 decoders can request 64 codec workers plus media
nodes, window loopers and system work. Actual worker creation,
runnability and scheduling contention are not yet measured.
Before revising the catch-up policy again, isolate this variable.

Opt-in haiku-lab-h264-single-thread limits requested parallelism to
one for known positive dimensions up to 640x480, H.264 video only.
Applied after container properties, before avcodec_open2.
No audio, HD, unknown-size or other codec treatment. Default unchanged.
Independent haiku-lab-video-thread-stats reports codec, dimensions,
original/requested/effective thread_count and active_thread_type
after successful open. Reports are per negotiation, not per stream
or proof of actual worker count. Thread count 1 may change decoder
latency, memory use and buffering; do not assume correctness.

Acceptance: native fixed-frame digest and timestamps for identical
fixture OFF/ON, lifecycle smoke with seek/pause, then balanced
4/8/16 SD trials. Keep deferred rendering fixed OFF initially and
catch-up OFF, then independent paired tests with deferred ON if
warranted. Compare valid playback, query tails, draw requests,
frame-gap timeouts and host load. HD untouched. No kernel change.
