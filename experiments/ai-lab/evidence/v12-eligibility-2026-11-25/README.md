# V12 native eligibility smoke
Image 5581c34f, 4 vCPU/8 GiB HVF, identical eligibility binary.
28 cases, all passed. Exactly two server acknowledgments and two
matching client skip records (256 KiB and 1 MiB) in enabled lab
allocation run only. No warm/ack/skip in ordinary or disabled cases.
Pixel and initial byte checks passed, including live neighbor.
Full mixed-version, pressure and lifecycle acceptance still pending.
