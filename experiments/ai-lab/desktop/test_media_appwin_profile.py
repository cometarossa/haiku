import unittest
from appwin_profile import parse
from test_appwin_profile import fixture

def media_fixture(port=456):
    s=fixture(123,port).replace("LAB_APPWIN","LAB_MEDIA_APPWIN")
    i=s.index("LAB_MEDIA_APPWIN_END")
    return s[:i]+f"LAB_MEDIA_APPWIN team=123 port={port} phase=redraw n=2 us=60 max=51 ge50=1\nLAB_MEDIA_APPWIN team=123 port={port} phase=batch n=4 us=200 max=100 ge50=2\n"+s[i:]

class MediaProfileTest(unittest.TestCase):
    def test_isolation(self):
        log=fixture()+media_fixture()+media_fixture(457)
        self.assertEqual(len(parse(log,1,16)),1)
        self.assertEqual(len(parse(log,None,None,media=True)),2)
        self.assertEqual(parse(log,2,None,media=True)[0]["redraw"]["us"],60)
    def test_fail_closed(self):
        s=media_fixture()
        for bad in (s.replace("phase=redraw","phase=unexpected"),s.replace("normal=1","normal=0"),s+s):
            with self.assertRaises(ValueError):parse(bad,None,None,media=True)
