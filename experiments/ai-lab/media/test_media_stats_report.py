import unittest
from media_stats_report import parse, summarize

P = "LAB_MEDIA_PRODUCER thread=123 lock_timeouts=1 late=3 attempts=101 no_buffer=1 fills=100 fill_timeouts=2 fill_errors=1 end_buffers=1 suppressed=5 sent=94 send_errors=1 wait_us=15000 fill_us=500000 max_fill_us=10000 last_send_error=-1"
C = "LAB_MEDIA_CONSUMER received=92 inactive=1 late=2 target_calls=88 no_target=1 copy_bytes=0 copy_us=0 target_us=10000 first_target_us=123456"

class StatsTest(unittest.TestCase):
    def test_valid(self):
        out = summarize(parse(P + "\n" + C))
        self.assertEqual(out["producer"]["sent"], 94)
        self.assertEqual(out["consumer"]["target_calls"], 88)

    def test_request_conservation(self):
        with self.assertRaises(ValueError):
            parse(P.replace("attempts=101", "attempts=102"))

    def test_send_conservation(self):
        with self.assertRaises(ValueError):
            parse(P.replace("sent=94", "sent=93"))

    def test_consumer_conservation(self):
        with self.assertRaises(ValueError):
            parse(C.replace("received=92", "received=93"))

    def test_marker_off(self):
        self.assertEqual(summarize(parse("ordinary log"), False), {})
        with self.assertRaises(ValueError):
            summarize(parse(P), False)

    def test_missing_record(self):
        with self.assertRaises(ValueError):
            summarize(parse(P))

    def test_duplicate_field(self):
        with self.assertRaises(ValueError):
            parse(P + " sent=94")

    def test_last_error(self):
        with self.assertRaises(ValueError):
            parse(P.replace("last_send_error=-1", "last_send_error=0"))

    def test_first_target(self):
        with self.assertRaises(ValueError):
            parse(C.replace("first_target_us=123456", "first_target_us=0"))

    def test_interleaved(self):
        with self.assertRaises(ValueError):
            parse("prefix " + P)
