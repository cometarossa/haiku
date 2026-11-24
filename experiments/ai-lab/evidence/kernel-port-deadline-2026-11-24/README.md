# Port read deadline under competing reader
AI-assisted independent Haiku research fork only. Identical executable
compiled on beta6 and checksum-verified on V3 ai_7d5672a7.
Two threads pinned to vCPU 0; normal-priority thread repeatedly writes
and drains messages while lower-priority thread waits on read_port_etc
or port_buffer_size_etc. Relative and absolute 150ms deadlines,
three trials per API/mode per guest. All 24 trials returned B_TIMED_OUT
and elapsed 150.112--151.300ms, with 3--4 intervening drains each.
No userspace deadline-extension defect reproduced in this scenario.
Source inspection explains why: both user syscall wrappers call
syscall_restart_handle_timeout_pre(flags, timeout), converting finite
positive relative deadlines to absolute deadlines before entering port.cpp.
This does not prove internal kernel callers have identical guarantees,
nor directly trace each wakeup. No kernel patch proposed from this test.
