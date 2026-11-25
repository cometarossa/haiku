import unittest
from bitmap_warm_pairs import paired


class PairedTests(unittest.TestCase):
    @staticmethod
    def row(state, value):
        return dict(mode="threads", surfaces=2, flag=state, render_us=value,
                    lifecycle_us=value, max_setup_us=value)

    def test_paired_ratios(self):
        r = self.row
        rows = [r("off",100), r("warm",80), r("single",90),
                r("warm",240), r("single",150), r("off",200)]
        results = list(paired(rows))
        single = next(x for x in results if x["metric"]=="lifecycle_us"
                      and x["treatment"]=="single" and x["reference"]=="off")
        self.assertEqual(single["blocks"], 2)
        self.assertEqual(single["median_ratio"], .825)
        self.assertEqual(single["min_ratio"], .75)
        self.assertEqual(single["max_ratio"], .9)
        self.assertEqual(single["wins"], 2)

    def test_partial_triplet_ignored(self):
        self.assertEqual(list(paired([self.row("off",100)])), [])

    def test_duplicate_state(self):
        with self.assertRaises(ValueError):
            list(paired([self.row("off",100)]*3))


    def test_quiet_comparison(self):
        r = self.row
        result = list(paired([r("off",100),r("single",110),r("quiet",80)], True))
        row = next(x for x in result if x["metric"]=="lifecycle_us"
                   and x["treatment"]=="quiet" and x["reference"]=="single")
        self.assertEqual(row["median_ratio"], .7273)
        with self.assertRaises(ValueError):
            list(paired([r("off",100),r("warm",110),r("single",80)], True))
