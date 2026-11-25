"""Host-side regression tests for V11 bitmap evidence validation."""
import unittest
from bitmap_warm_smoke import verify_client, parse


class BitmapWarmTests(unittest.TestCase):
    def setUp(self):
        self.rows = ["threads,2,64,0,2048,0,20,25,65536,0,5,40,0",
                     "threads,2,64,1,2048,3,25,25,65536,0,6,40,0"]

    def test_two_surface(self):
        self.assertEqual(verify_client("\n".join(self.rows), "threads", 2, 64),
                         dict(render_us=25, lifecycle_us=40, max_setup_us=6))

    def test_duplicate_worker(self):
        with self.assertRaises(ValueError):
            verify_client("\n".join([self.rows[0], self.rows[0]]), "threads", 2, 64)

    def test_pixel_mismatch(self):
        self.rows[1] = self.rows[1].replace("65536,0", "65536,1")
        with self.assertRaises(ValueError):
            verify_client("\n".join(self.rows), "threads", 2, 64)

    def test_white_mismatch(self):
        self.rows[1] = self.rows[1][:-1] + "1"
        with self.assertRaises(ValueError):
            verify_client("\n".join(self.rows), "threads", 2, 64)

    def test_team_count(self):
        data = ("LAB_BITMAP_WARM team=7 token=1 bytes=262144 us=10\n"
                "LAB_BITMAP_WARM team=7 token=2 bytes=262144 us=11\n")
        self.assertEqual(len(parse(data, 2, "threads")), 2)
        with self.assertRaises(ValueError):
            parse(data, 2, "teams")
        with self.assertRaises(ValueError):
            parse(data, 0, "threads")

    def test_duplicate_token(self):
        line = "LAB_BITMAP_WARM team=7 token=1 bytes=262144 us=10\n"
        with self.assertRaises(ValueError):
            parse(line * 2, 2, "threads")
