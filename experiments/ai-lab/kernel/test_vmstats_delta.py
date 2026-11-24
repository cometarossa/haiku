import unittest
from vmstats_delta import snapshots, deltas

def snap(n, enabled=1, extra=""):
    return f"LAB_VM enabled={enabled} locks={n} lock_wait_us={n*2} empty_flushes={n}\nLAB_VM flushes={n} flush_us={n} invalid_pages={n} remote_candidates={n}\n" + extra

class TestVMStats(unittest.TestCase):
    def test_v6(self):
        rows = list(snapshots((snap(2)+snap(7,0)).splitlines()))
        d = list(deltas(rows))[0]
        self.assertEqual(d["LAB_VM.lock_wait_us"],10)
        self.assertEqual(d["enabled_end"],0)
    def test_reset(self):
        with self.assertRaises(ValueError):
            list(deltas(list(snapshots((snap(7)+snap(2)).splitlines()))))
    def test_incomplete(self):
        with self.assertRaises(ValueError):
            list(snapshots(["LAB_VM enabled=1 locks=3"]))
    def test_v7(self):
        def extra(n):
            return f"LAB_VM_WAIT outer={n} wait_us={n*3} ge50us={n} ge1ms=0\nLAB_VM_HOLD samples={n} hold_us={n*4} ge50us={n} ge1ms=0\n"
        d = list(deltas(list(snapshots((snap(2,1,extra(2))+snap(5,0,extra(5))).splitlines()))))[0]
        self.assertEqual(d["LAB_VM_HOLD.hold_us"],12)
    def test_bad_bins(self):
        def extra(n):
            return f"LAB_VM_WAIT outer={n} wait_us=0 ge50us=0 ge1ms={n}\nLAB_VM_HOLD samples={n} hold_us=0 ge50us=0 ge1ms=0\n"
        with self.assertRaises(ValueError):
            list(deltas(list(snapshots((snap(2,1,extra(2))+snap(5,0,extra(5))).splitlines()))))
    def test_v7b_archived_windows(self):
        from pathlib import Path
        root = Path(__file__).resolve().parent.parent / "evidence" / "kernel-v7b-handoff-repeat-2026-11-24"
        import csv
        with (root / "combined-summary.csv").open() as f:
            rows = list(csv.DictReader(f))
        for row in rows:
            path = root / ("{}-{}-{}.txt".format(row["mode"], row["cpus"], row["repeat"]))
            if not path.exists():
                continue
            with self.subTest(path=path.name):
                d = list(deltas(list(snapshots(path.read_text().splitlines()))))[0]
                self.assertEqual(d["mutex_enabled_start"], 1)
                self.assertEqual(d["mutex_enabled_end"], 0)
                for key, value in d.items():
                    if key.startswith("LAB_"):
                        self.assertEqual(value, int(row[key]))
        self.assertEqual(len(list(root.glob("*-[23].txt"))), 6)

    def test_v7b_invalid_window(self):
        from pathlib import Path
        path = Path(__file__).resolve().parent.parent / "evidence" / "kernel-v7b-handoff-repeat-2026-11-24" / "threads-4-2.txt"
        raw = path.read_text()
        for bad in (raw.replace("samples=4999 invalid=0", "samples=4999 invalid=1"),
                    raw.replace("ge50us=4973 ge1ms=8", "ge50us=4973 ge1ms=99999"),
                    raw.replace("LAB_MUTEX enabled=0", "LAB_MUTEX enabled=2")):
            self.assertNotEqual(raw, bad)
            with self.assertRaises(ValueError):
                list(deltas(list(snapshots(bad.splitlines()))))

if __name__ == "__main__":
    unittest.main()
