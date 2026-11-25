import tempfile
import unittest
from pathlib import Path
from media_stats_smoke import validate
from test_media_stats_report import P, C


class SmokeValidationTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.write("done.txt", "0\n")
        self.write("revision.txt", "hrev60465+ai_db20e3f2\n")
        for state in ("off", "on"):
            self.write(state+".exit", "0\n")
            self.write(state+".start", "100000\n")
            self.write(state+".stop", "5000000\n")
            self.write(state+".positions", "".join(
                f"SAMPLE {i}\ntrue\nReply BMessage(B_REPLY):\n"
                f'    "result" (B_INT64_TYPE) : {i*1000000} (0x0)\n'
                for i in range(1,4)))
            log = "LAB_MEDIA_OVERLAY_PREFLIGHT software format=8\n"
            if state == "on":
                log += P+"\n"+C+"\n"
            self.write(state+".log", log)

    def write(self, name, data):
        (self.root/name).write_text(data)

    def test_good_pair(self):
        rows = validate(self.root, "db20e3f2")
        self.assertEqual(rows["off"]["stats"], {})
        self.assertEqual(rows["on"]["stats"]["producer"]["sent"],94)

    def test_wrong_revision(self):
        with self.assertRaises(ValueError):
            validate(self.root, "63cc5489")

    def test_wrong_treatment(self):
        self.write("off.log", "trying without overlays\n")
        with self.assertRaises(ValueError):
            validate(self.root, "db20e3f2")

    def test_first_target_outside_interval(self):
        self.write("on.start", "200000\n")
        with self.assertRaises(ValueError):
            validate(self.root, "db20e3f2")

    def test_no_advance(self):
        p = self.root/"on.positions"
        p.write_text(p.read_text().replace("3000000", "2000000"))
        with self.assertRaises(ValueError):
            validate(self.root, "db20e3f2")

    def test_incomplete(self):
        self.write("done.txt", "1\n")
        with self.assertRaises(ValueError):
            validate(self.root, "db20e3f2")
