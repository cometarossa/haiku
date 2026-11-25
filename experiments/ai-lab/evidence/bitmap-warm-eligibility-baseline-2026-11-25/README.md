# V11 bitmap eligibility and isolation baseline
AI-assisted independent fork. Native identical executable on Beta6
and V10 12b5c9ec, both without V11 code. Seven cases each for lab and
ordinary signatures: eligible RGB32 256x256, exact 1 MiB boundary,
2 MiB excluded size, no clear flag, RGB16, no views, live neighboring
allocation sentinel. RGB32 views draw a 16x16 rectangle and check
all other pixels unchanged. 15220736 initial/sentinel byte checks,
3670016 RGB checks, 28 cases, no errors. Does not prove actual shared
page adjacency. Marker absent; no V11 eligibility behavior validated.
Next use identical binary with V11b OFF/ON and count only two warm
records (262144 and 1048576 bytes) in enabled lab-signature run;
zero for ordinary or OFF. Overlay/clone and resource pressure remain
untested. No performance claims.
