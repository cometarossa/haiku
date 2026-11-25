import unittest
from port_queue_report import parse,summarize

A="""port: total: 1000, used: 20, left: 980

TEAM   23 (/boot/system/servers/app_server):
   ID                         name  capacity  queued
----------------------------------------------------
   42                video window       100      99
   44                another port        20       0

TEAM 45 (MediaPlayer):
   ID                         name  capacity  queued
----------------------------------------------------
   99                       window       100     100
"""


class PortQueueTest(unittest.TestCase):
    def test_isolate_team(self):
        self.assertEqual(parse(A,23)[42],dict(name="video window",capacity=100,queued=99))
        self.assertNotIn(99,parse(A,23))
    def test_full_sample(self):
        r=summarize([(100,A),(200,A.replace("100      99","100     100"))],23)
        self.assertEqual(r["ports"][42]["full"],1)
        self.assertEqual(r["ports"][42]["max_queued"],100)
        self.assertEqual(r["ports"][42]["observations"],2)
    def test_invalid(self):
        for s in (A.replace("100      99","100     101"),
                  A.replace("20       0","0       0"),
                  A.replace("   44","   42"), A.replace("video window","video window x\n")):
            with self.assertRaises(ValueError):parse(s,23)
        with self.assertRaises(ValueError):parse(A,999)
        with self.assertRaises(ValueError):summarize([(200,A),(100,A)],23)
        with self.assertRaises(ValueError):summarize([(100,A),(200,A.replace("video window","other title"))],23)
