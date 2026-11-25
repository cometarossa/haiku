import unittest
from bitmap_reply_verify import verify_reply


class ReplyTests(unittest.TestCase):
    def test_quiet(self):
        self.assertEqual(verify_reply("25,25,262144,0,0", "lab", "quiet"),
                         {"flags": 25, "checked": 262144})

    def test_ordinary(self):
        self.assertEqual(verify_reply("1,1,0,0,0", "ordinary", "quiet"),
                         {"flags": 1, "checked": 0})

    def test_missing_ack(self):
        with self.assertRaises(ValueError):
            verify_reply("25,17,262144,0,0", "lab", "quiet")

    def test_bad_bytes(self):
        with self.assertRaises(ValueError):
            verify_reply("25,25,262144,1,0", "lab", "quiet")
