# Anonymous area lifecycle baseline
AI-assisted independent research fork. Beta6 and V5 ai_8f8e7d06;
same native executable checksum-verified. 21 runs per guest, 48 worker
rows per guest. Requested per-worker affinity, independent areas
within a single team, B_NO_LOCK; zero contents tested at both ends of
each page, two words written, clone alias verified and modified,
original deleted, clone contents verified again. 178944 successful
page-level alias checks across both guests. Timings include initial
touch and zero checks; verification includes clone first access and
write/read alias check. Final deletion timing excludes deletion of
the original area. These are not raw page-fault times or bandwidth.
The initial beta run was incomplete at four workers x8192 pages;
partial CSV preserved, exact failure status was not captured.
Bounded revision excluded this case and completed all 42 runs.
No controlled host-load or native hardware claim; affinity request
succeeded but residency not continuously verified. Concurrent
results may reflect VM/TLB effects and address-space/cache locking.
Investigate before modifying VM internals.
