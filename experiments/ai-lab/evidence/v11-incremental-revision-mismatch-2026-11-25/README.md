# V11 incremental build identity mismatch
AI-assisted independent fork. Local a5ad26fd artifact built successfully,
checksums verified and booted in disposable overlay on VNC 5916.
First OFF workload returned valid drawing rows, but uname identified
the previous V10 revision 12b5c9ec. Harness rejected it before enabling
the experiment. No ON results or V11 performance claims. Original
artifact and logs retained; not an accepted V11 image.
Build log shows ServerApp.o and app_server rebuilt. Zima's generated/
build/haiku-revision still contained hrev60465+ai_12b5c9ec. Jam's
DetermineHaikuRevision2 action (explicit override) has no input
dependency; the old generated revision survives incremental builds.
Local builder now refreshes the generated revision atomically if
needed, checks it again after Jam. A new commit and artifact are needed;
actual uname and ON/OFF marker counts remain acceptance requirements.
