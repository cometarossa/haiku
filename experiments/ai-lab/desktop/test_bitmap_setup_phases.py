import unittest

from bitmap_setup_phases import verify_phases, slowest_setup_worker, paired_phase_deltas


class SetupPhaseTests(unittest.TestCase):
    def setUp(self):
        self.rows = ["threads,2,64,0,2048,0,20,25,65536,0,5,40,0,1,1,1,1,1",
                     "threads,2,64,1,2048,3,25,25,65536,0,6,40,0,2,1,1,1,1"]

    def test_valid(self):
        summary, workers = verify_phases("\n".join(self.rows), "threads", 2, 64)
        self.assertEqual(summary["max_setup_us"], 6)
        self.assertEqual(workers[1]["constructor_us"], 2)

    def test_inconsistent_sum(self):
        self.rows[0] = self.rows[0][:-1] + "2"
        with self.assertRaises(ValueError):
            verify_phases("\n".join(self.rows), "threads", 2, 64)

    def test_negative_duration(self):
        self.rows[0] = self.rows[0].replace(",1,1,1,1,1", ",-1,3,1,1,1")
        with self.assertRaises(ValueError):
            verify_phases("\n".join(self.rows), "threads", 2, 64)

    def test_legacy_pixel_failure(self):
        self.rows[0] = self.rows[0].replace("65536,0", "65536,1")
        with self.assertRaises(ValueError):
            verify_phases("\n".join(self.rows), "threads", 2, 64)


    def test_select_worker_not_independent_maxima(self):
        _, workers = verify_phases("\n".join(self.rows), "threads", 2, 64)
        self.assertEqual(slowest_setup_worker(workers)["worker"], 1)

    def test_paired_deltas(self):
        _, workers = verify_phases("\n".join(self.rows), "threads", 2, 64)
        def row(flag, extra):
            phases = [dict(x, constructor_us=x["constructor_us"] + extra) for x in workers]
            return dict(flag=flag, mode="threads", surfaces=2, phases=phases,
                        max_setup_us=6+extra, lifecycle_us=40+extra, render_us=25)
        result = list(paired_phase_deltas([row("off",0),row("warm",3),row("single",1)]))
        self.assertEqual(result[0]["constructor_delta_us"],3)
        self.assertEqual(result[0]["setup_delta_us"],3)
        self.assertEqual(result[1]["pre_render_delta_us"],1)
        with self.assertRaises(ValueError):
            list(paired_phase_deltas([row("off",0),row("warm",3)]))
