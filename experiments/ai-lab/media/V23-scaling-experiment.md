# V23 candidate: isolate bitmap scaling cost
V22 observation counters demonstrate the decoder/rendering tradeoff.
Before a new scheduling policy, isolate an existing graphics option.
MediaPlayer Settings::Get defaults scaleBilinear to true;
VideoView::_DrawBitmap passes B_FILTER_BITMAP_BILINEAR to DrawBitmapAsync.
ServerWindow forwards this flag to DrawingEngine::DrawBitmap and
BitmapPainter selects its existing bilinear or nearest-neighbor OP_COPY
scaled path. No-scale path may bypass the filter; verify actual scale
before making claims. B_WAIT_FOR_RETRACE is commented out in ServerWindow.
No system-wide quality or scheduling changes.

Native helper reads a flattened existing settings BMessage, writes a
distinct exclusive output, reopens it and verifies scaleBilinear. It does
not write the active file itself. A future runner must preserve and
restore original settings bytes, reject absent/unexpected state and
symlinks, ensure MediaPlayer is stopped before settings swaps, validate
the requested setting, archive failures and verify restored hash.
Keep fixture, window geometry, decoder threads, rendering mode and
diagnostics identical; compare balanced bilinear/nearest/nearest/bilinear
at four streams before escalating. Quantify the quality tradeoff;
nearest-neighbor is not automatically an acceptable production default.
Observe draw completions, decoder timeout fraction, successful queries,
per-window idle bins and shutdown elapsed. No physical FPS inference.
