import unittest
from v22_observation_distribution import distribution


class DistributionTest(unittest.TestCase):
    def test_counts_and_idle_bins(self):
        def row(bins):
            return dict(anchor=1000000,created=1100000,ended=5100000,bins={
                k:[0,0,0,0,0,v,0,0] for k,v in bins.items()})
        r={("view",1):row({1000000:99,2000000:30,4000000:90}),
           ("view",2):row({2000000:5,3000000:1})}
        d=distribution(r,"view",5,2000000,4000000)
        self.assertEqual(d["instance_totals_sorted"],[6,30])
        self.assertEqual(d["per_second"],[35,1])
        self.assertEqual(d["total"],36)
        self.assertEqual(d["zero_instance_seconds"],1)
        self.assertEqual(d["median_instance"],18)
        with self.assertRaises(ValueError):distribution(r,"view",5,1000000,4000000)
        with self.assertRaises(ValueError):distribution(r,"producer",0,2000000,4000000)
