# V12 single white initialization experiment
AI-assisted independent fork. Private allocation reply bit 0x8 indicates
a completed full server white fill; no new message fields or public ABI.
V11 marker retains redundant clear; separate marker
/boot/home/config/settings/haiku-lab-bitmap-single-clear enables V12.
Both absent by default. Existing lab signature retained for identical
binary comparisons. New server verifies allocator, flags, RGB32, <=1 MiB,
area bounds, exact row size and extent before acknowledging. New client
skips only after a successful mapping and valid reply fields with exact
allocator+ack bits, expected flags/color/size. Old server sends no bit;
old client ignores bit and still clears. Reconnect, malloc, overlay and
noneligible allocations retain original paths. Mixed-version behavior
requires verification, not assumed tested. Logs distinguish server ack
and actual client skip, matching team/token/length. Logs add overhead.
Acceptance: isolated boot; 28 eligibility cases including ordinary,
same binary, off/V11/V12, 1/2/4 surfaces, threads/teams, batch64 then
1/1024; byte/pixel validation; zero ack/skip when disabled or excluded;
matching exactly one ack+skip per eligible allocation; cleanup markers.
Add padded row, CMAP8, no-server-link, clone, overlay and churn tests.
Do not enable globally or claim benefit until repeated complete lifecycle
and pressure/desktop regression tests pass. No page fault attribution.
