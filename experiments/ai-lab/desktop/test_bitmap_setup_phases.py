import unittest

from bitmap_setup_phases import verify_phases


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
