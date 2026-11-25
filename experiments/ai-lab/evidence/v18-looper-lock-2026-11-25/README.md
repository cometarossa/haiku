# V18 isolated BLooper post-timeout path
Native V18 fb8c2e41; probe source 9a90e005, binary SHA256 retained.
One deliberate B_TIMED_OUT acquisition leaves the idle count at 1
instead of 0. Six alternating 50,000-iteration clean/timed pairs,
600,000 uncontended lock/unlock operations, all stable counts and
exit 0. This confirms the retained semaphore path and its overhead.
The absolute difference is sub-microsecond, insufficient by itself
to explain seconds of media scripting latency. No inference about
contention or actual lock ownership; host not isolated. Keep the
race-avoiding algorithm unchanged. Next: persistent window query
smoke and separate IPC queue observations under media workload.
