# V9 Interface Kit bitmap send coalescing candidate
AI-assisted independent research fork. Preserve BView synchronous bitmap
draw semantics: queue AS_VIEW_DRAW_BITMAP, then existing Sync sends
AS_SYNC and waits for its reply. The server processes messages in order.
Outside view transactions, old wrappers flushed the drawing command
before Sync (two sends when buffer has space); new wrappers may combine
them into one port packet. The sender may still auto-flush at boundaries.
Async entry points retain their existing FlushIfNotInTransaction behavior.
Invalid synchronous arguments retain the existing barrier. Private
nonvirtual helper adds no instance data or vtable slots.

Build regular x86_64 and boot isolated image; compare same native binary
on V8 off and V9 off. bitmap_sync_lifetime tests four synchronous overloads
in and out of an offscreen window transaction; verify each final RGB pixel
with immediate source reuse, and confirm transaction state. Test the
ordinary onscreen window path, clipping, scaling, tiled drawing, picture
recording, resource deletion, invalid args, and buffer boundary cases.
Use actual IPC packet counts to confirm fewer sends, not just elapsed
time. Repeat under matched host conditions and check desktop/media/IPC
regressions. Do not assume earlier offscreen FillRect batching results
predict this change: offscreen windows start in a transaction, and that
test used explicit Sync rather than synchronous bitmap drawing.
No performance claim until native guest tests and comparisons complete.
