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

## Independent server wire probe
bitmap_reply_probe.cpp uses the private application link to create one
normal RGB32 bitmap and reads the actual allocation reply. For enabled
lab treatments it clones the area read-only, checks the bounded extent
and all 262144 bytes before any client fill, then releases both resources.
Expected literal reply bits: off/warm 0x01, single 0x09, quiet 0x19;
ordinary app always 0x01. Warm/single/quiet lab must already be white.
This confirms server acknowledgment and pre-fill independently of logs;
it does NOT prove the public BBitmap client actually skipped memset.
Native build and test pending, private header/symbol availability unverified.
