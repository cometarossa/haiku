# V12 balanced corrected-clock comparison
Same V12 image 5581c34f, corrected native binary, 36 verified runs,
108 workers, 147456 fills, 7077888 final pixel checks, 28311552 initial
byte checks, 72 warm records, 36 matched V12 ack/skip pairs, no errors.
Three balanced blocks per topology. Ratios are medians of within-block
ratios, not ratios of pooled medians. Single clear improves rendering
in all 12 paired blocks, but only threads4 shows a median lifecycle
improvement. V11 warm beats V12 lifecycle in both four-worker topologies
in all three blocks. Host load uncontrolled; serial output differs by
treatment. No global performance claim. V13 quiet control pending.
