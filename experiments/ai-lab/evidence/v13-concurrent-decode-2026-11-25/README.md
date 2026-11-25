# V13 native concurrent decode correctness
Same previously compiled Beta6 decoder, hashed fixture and binary.
1, 2, 4 separate decoders, 7 total, 1050 frames of 1280x720 H.264.
All exit zero with identical active-byte FNV-1a64 digest matching
Beta6 reference. Not timed, no presentation or audio measurement.
Native GUI overlay failure is separate. Host not isolated.
