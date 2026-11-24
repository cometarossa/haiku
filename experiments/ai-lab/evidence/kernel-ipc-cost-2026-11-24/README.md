# Single-thread nonblocking IPC cost baseline
AI-assisted independent research fork only. Haiku beta6 and V2
(d800dd54), QEMU/HVF, same native binary compiled on beta6 and
checksum-verified on V2. One thread alternates writes and reads
or writes and drains batches of 64, on a 64-slot port, with
zero relative timeout. Payload sizes 0, 64, 4096 bytes.
4096 messages per run, three repeats per configuration and guest.
All 147456 messages verified, including code, length and payload.
No errors or deliberate waits. Elapsed time includes syscalls,
allocation, copying, locks and verification; it does not isolate
any individual kernel operation. Guest scheduling and host load
are not controlled. Do not claim native performance or a regression
from between-guest differences. Next isolate blocking handoffs
and instrument lock wait and allocation separately.
