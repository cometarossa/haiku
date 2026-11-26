# V21 balanced native frame digest repeat
Image 2f9d27bf, eight runs OFF/ON/ON/OFF twice. All 4800 frames
and timestamps match; effective thread_count four vs one.
Median decode+hash+startup time OFF 393539 us, ON 404437 us;
median paired OFF/ON ratio 0.94843. Initial 2.8x smoke speedup
not reproduced, likely order/warm-up/host variation; no causal
attribution to cache alone. No physical display or concurrent
performance claim. Initial repeat aborted at upload HTTP 400
because URL lacked trial index; guest returned to prompt, runner
stopped, corrected aa49a3f8 and restarted with separate directory.
No result from aborted run included. Native cleanup confirmed.
