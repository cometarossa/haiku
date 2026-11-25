# V13 quiet single-clear diagnostic control
Independent experimental fork, off by default. Same image comparison:
OFF, V12 single-clear traced, V13 single-clear quiet. The quiet marker
/boot/home/config/settings/haiku-lab-bitmap-quiet is honored only with
the existing single-clear marker and an eligible fully acknowledged
allocation. Private reply bit 0x10 accompanies 0x8; never valid alone.
No public ABI or message size change. Server and client suppress only
these three lab trace lines, not kernel diagnostics globally. Old clients
that require exact 0x9 fall back to their original clear with 0x19.
The fallback remains traced if server extent validation fails.
Both traced/quiet acknowledged paths perform the same server marker
lookup and fill. Quiet still measures the server fill clock. Native
eligibility, boot, mixed-client and performance tests pending.
No trace in quiet runs is NOT independent proof of the client skip.
Require separate raw reply-bit verification or low-overhead audit before
accepting attribution. White and RGB correctness alone cannot prove
single initialization. Preserve all historical measurements.
