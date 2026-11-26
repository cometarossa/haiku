# V23 scaling settings read-only native smoke
V22 image 4ae8e7ea; helper compiled from 83f428d4.
Original settings scaleBilinear=0, despite source default true.
Both variants generated, re-read and overwrite rejected.
Original active settings compared byte-for-byte to backup;
SHA-256 identical before/after. No active setting changed.
Previous experiments did not record effective scaling flags;
do not retroactively assert that all prior trials used nearest.
