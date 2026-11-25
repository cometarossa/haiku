# V13 independent boot and raw wire verification
Image 97075eae, 1681 targets, source and Mac compressed/raw SHA-256
verified. QEMU HVF 4 vCPU/8 GiB, independent overlay, display 21.
Desktop and Terminal observed. Same native probe that failed on the
older Beta6 completed all eight cases on V13; lab flags 1/1/9/25
for OFF/warm/single/quiet; ordinary flags always 1. Read-only
inspection verifies 786432 initial bytes before any client fill.
This establishes server prefill and acknowledgment independently of
trace logs, not independent proof of client memset omission.
Public BBitmap eligibility and quiet performance pending.
