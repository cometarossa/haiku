# Corrected native lifecycle benchmark provenance
Source correction b3d306f7 (earliest setup across all workers).
Compiled natively on Beta6 using recorded compiler; exact source and
binary hashes verified. Two signedness warnings in existing bounded
bitmap checks; no compile failure. Binary retained in separate Mac
guest-results/drawing-white-lifecycle-corrected-20261125 directory.
The historical binary and historical evidence remain unchanged.
New balanced campaign executes identical corrected binary on 5581c34f
in OFF, warm (V11) and single (V12) states.
