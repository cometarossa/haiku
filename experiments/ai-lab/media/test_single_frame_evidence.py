"""Fork-only validation of a real before/after MediaPlayer regression."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = ROOT / "experiments/ai-lab/evidence/media-player-single-frame-2026-11-23"
SUPPLIER_CPP = ROOT / "src/apps/mediaplayer/supplier/MediaTrackVideoSupplier.cpp"
SUPPLIER_H = ROOT / "src/apps/mediaplayer/supplier/MediaTrackVideoSupplier.h"


class SingleFrameIsolationRegression(unittest.TestCase):
    def test_before_and_after_native_guest_outputs(self):
        before = (EVIDENCE / "single_baseline.stdout").read_text()
        after = (EVIDENCE / "single_patched.stdout").read_text()
        self.assertIn("track_frames=1,1", before)
        self.assertIn("track_frames=1,1", after)
        self.assertIn("first,status=0,was_cached=0,wrote_pixels=1", before)
        self.assertIn("first,status=0,was_cached=0,wrote_pixels=1", after)
        self.assertIn("second,status=0,was_cached=1,wrote_pixels=0", before)
        self.assertIn("SINGLE_FRAME_INDEPENDENT_SUPPLIERS_FAIL", before)
        self.assertIn("second,status=0,was_cached=0,wrote_pixels=1", after)
        self.assertIn("SINGLE_FRAME_INDEPENDENT_SUPPLIERS_PASS", after)

    def test_fork_uses_per_instance_cache_flag(self):
        source = SUPPLIER_CPP.read_text()
        header = SUPPLIER_H.read_text()
        self.assertNotIn("static int already", source)
        self.assertIn("fSingleFrameAlreadyRead(false)", source)
        self.assertIn("if (singleFrame && fSingleFrameAlreadyRead)", source)
        self.assertIn("bool\t\t\t\tfSingleFrameAlreadyRead;", header)

    def test_extended_independent_covers_and_cache_reuse(self):
        import re
        for kind in ("same", "distinct"):
            output = (EVIDENCE / ("single_extended_%s.stdout" % kind)).read_text()
            self.assertIn("track_frames=1,1", output)
            self.assertIn("SINGLE_FRAME_INDEPENDENT_SUPPLIERS_PASS", output)
            for label in ("first", "second"):
                match = re.search(
                    r"^%s,status=0,was_cached=0,wrote_pixels=1,hash=([a-f0-9]{16})$"
                    % label, output, re.M)
                self.assertIsNotNone(match, label + " first decode")
                self.assertIn(
                    "%s_again,status=0,was_cached=1,wrote_pixels=0" % label,
                    output)
            digests = re.findall(
                r"^(?:first|second),status=0,was_cached=0,wrote_pixels=1,"
                r"hash=([a-f0-9]{16})$", output, re.M)
            self.assertEqual(len(digests), 2)
            if kind == "distinct":
                self.assertNotEqual(digests[0], digests[1])
            else:
                self.assertEqual(digests[0], digests[1])

    def test_cache_activation_after_decode(self):
        source = SUPPLIER_CPP.read_text()
        self.assertLess(
            source.index("ret = fVideoTrack->ReadFrames("),
            source.index("fSingleFrameAlreadyRead = true;"))


if __name__ == "__main__":
    unittest.main()
