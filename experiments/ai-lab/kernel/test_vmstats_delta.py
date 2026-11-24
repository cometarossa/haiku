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
if __name__ == "__main__":
    unittest.main()
