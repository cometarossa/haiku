# V13 independent client fill audit
8/8 positive and negative native controls passed on 97075eae. LD_PRELOAD
interposed the actual matching 256 KiB white memset to BBitmap::Bits()
on the constructor thread. OFF and warm lab: one fill; single and quiet
lab: zero fills; all four ordinary controls: one fill. Every case
checked 262144 bytes white (2097152 total), zero errors. Compiled on
Beta6, hashes verified on V13. The V13 native compile attempt failed
because g++ is not installed; failure recorded, no system package changes.
This is diagnostic-only evidence for this exact allocation size and
path, not exhaustive proof for all sizes or inlined/non-memset writes.
No interposer was used in performance runs. Default still unchanged.
