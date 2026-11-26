import unittest
from v21_paired_summary import aggregate

def row(state, valid=True):
    return dict(tag=state,state=state,valid=valid,probe=dict(attempted=36,errors=0,expected=36,
        by_operation={"Position":{"p95_us":100}}),view=dict(draw=100,looper_fail=2),
        diagnostics=dict(proxy=dict(gap_timeout=5),media=dict(producer=dict(fills=100,fill_timeouts=5),
        consumer=dict(late=3))),lifetime_to_quit_request_us=25000000,observation_us=20000000)

class PairedSummaryTest(unittest.TestCase):
    def test_balanced(self):
        r=dict(complete=True,all_diagnostic_valid=True,all_playback_valid=False,
            rows=[row("off"),row("on",False),row("on"),row("off")])
        a=aggregate(r)
        self.assertEqual(a["groups"]["off"]["fill_timeout_fraction"],.05)
        self.assertEqual(a["groups"]["on"]["valid_playback_trials"],1)
        self.assertEqual(a["groups"]["off"]["draw_requests_per_lifetime_second"],4)
        self.assertFalse(a["pairs"][0]["both_playback_valid"])
        self.assertTrue(a["pairs"][1]["both_playback_valid"])
        r["complete"]=False
        with self.assertRaises(ValueError):aggregate(r)


    def test_no_position_under_saturation(self):
        bad=row("off",False)
        bad["probe"]=dict(attempted=3,errors=3,expected=36,by_operation={"Title":{"p95_us":2000000}})
        r=dict(complete=True,all_diagnostic_valid=True,all_playback_valid=False,
            rows=[bad,row("on"),row("on"),row("off")])
        a=aggregate(r)
        self.assertEqual(a["groups"]["off"]["position_p95_us"],[None,100])
        self.assertEqual(a["groups"]["off"]["failed_queries"],3)
        self.assertEqual(a["groups"]["off"]["not_attempted_queries"],33)
        self.assertFalse(a["pairs"][0]["both_playback_valid"])
