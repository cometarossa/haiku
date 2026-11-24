# Demand paging versus fully wired anonymous areas
AI-assisted independent research fork. Beta6 and V5 ai_8f8e7d06,
same native executable SHA256 checked in V5. Four workers in one
team, verified affinity and barriers between phases, B_NO_LOCK
versus B_FULL_LOCK, three repeats per configuration. Initial read
checks zero contents at page ends, second access writes patterns,
resident verification checks them, then each area is deleted.
72 runs, 288 worker rows, 129024 page checks; no reported errors.
Report the per-worker median of create + first-read durations,
not a sum of medians, nor aggregate throughput. Fully wired areas
avoid demand page faults but consume nonpageable physical memory
and differ in VM semantics. Not a recommendation to change defaults
or wire arbitrary user allocations; at most a bounded-buffer strategy
and a diagnostic control for the forthcoming V6 counters. Guest
and host load uncontrolled, virtualization may magnify the gap.
No kernel change or native hardware performance claim.
