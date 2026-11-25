"""AI-assisted: synthetic parser tests, not native server validation."""
import unittest
from appwin_profile import parse


def fixture(team=123, port=456):
    result = []
    for p, n, us, maximum, slow in [
        ("window", 4, 8, 3, 0), ("desktop_read", 4, 60, 54, 1),
        ("desktop_write", 0, 0, 0, 0), ("dispatch", 20, 120, 70, 1),
        ("sync", 2, 75, 70, 1), ("fill", 16, 32, 2, 0),
        ("bitmap", 0, 0, 0, 0),
    ]:
        result.append(f"LAB_APPWIN team={team} port={port} phase={p} n={n} us={us} max={maximum} ge50={slow}")
    result.append(f"LAB_APPWIN_END team={team} port={port} normal=1")
    return "\n".join(result) + "\n"


class ProfileTests(unittest.TestCase):
    def test_ok(self):
        self.assertEqual(parse(fixture(), 1, 16)[0]["fill"]["n"], 16)

    def test_off(self):
        self.assertEqual(parse("ordinary serial log\n", 0, 0), [])

    def test_interleaved(self):
        rows = "\n".join(s for pair in zip(fixture().splitlines(),
                         fixture(123, 457).splitlines()) for s in pair)
        self.assertEqual(len(parse(rows, 2, 32)), 2)

    def test_truncated(self):
        with self.assertRaises(ValueError):
            parse(fixture().rsplit("LAB_APPWIN_END", 1)[0], 1, 16)

    def test_duplicate(self):
        with self.assertRaises(ValueError):
            parse(fixture() + fixture(), 1, 16)

    def test_bad_count(self):
        with self.assertRaises(ValueError):
            parse(fixture(), 1, 15)

    def test_abnormal(self):
        with self.assertRaises(ValueError):
            parse(fixture().replace("normal=1", "normal=0"), 1, 16)

    def test_bad_subset(self):
        with self.assertRaises(ValueError):
            parse(fixture().replace("n=20 us=120", "n=17 us=120"), 1, 16)

    def test_bad_metric(self):
        with self.assertRaises(ValueError):
            parse(fixture().replace("us=60 max=54 ge50=1", "us=60 max=54 ge50=0"), 1, 16)


if __name__ == "__main__":
    unittest.main()
