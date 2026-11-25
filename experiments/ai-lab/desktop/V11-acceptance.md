# V11 opt-in bounded server-side white bitmap initialization
AI-assisted independent research fork. No public API/ABI or protocol change.
After AS_CREATE_BITMAP allocation and successful _AddBitmap, before the
reply, ordinary allocator-backed RGB32 bitmaps with exactly
B_BITMAP_ACCEPTS_VIEWS|B_BITMAP_CLEAR_TO_WHITE and size 1..1 MiB are
eligible only for the V11 lab signature prefix and marker
/boot/home/config/settings/haiku-lab-bitmap-warm. Verify area bounds and
buffer pointer. The client still performs the original white clear.
No overlay, cloned client area, locked/contiguous or non-RGB32 buffer
is touched. No permanent memory wiring. Marker absent by default.
This intentionally redundant initialization is an experiment, not a
general performance fix. It moves work into creation; it may worsen
end-to-end latency, and logging also adds cost. Existing ordinary
applications are excluded. Do not enable globally.
Native drawing_white_lifecycle checks every initial byte is white,
then checks 65536 final RGB pixels per surface and reports constructor/
setup duration, drawing makespan, and earliest setup to final Sync.
Compare V10 and V11 using identical binary, V11 marker off/on, 1/2/4
surfaces, threads/teams, repeat paired with controlled host load.
Verify LAB_BITMAP_WARM exactly one per eligible allocation (size
262144 in benchmark), zero when off, remove marker after tests.
Additional negative tests: no clear flag, non-RGB32, oversize, nonlab
signature; preserve existing data, overlay and client-owned areas.
Full native build, boot and acceptance pending.
