# V21 four-stream decoder thread comparison
Image 2f9d27bf; OFF/ON/ON/OFF. All four trials pass playback
and diagnostic gates. H.264 SD, 4 versus 1 configured decoder
thread, deferred rendering and catch-up OFF throughout.
Actual QEMU command lines confirm 4 vCPU/8192 MiB per guest.
All three guest PIDs stable; host is not isolated.
Full native logs, paired summaries and SHA256 manifest retained.
Counts cover node lifetimes; no physical FPS claim.
