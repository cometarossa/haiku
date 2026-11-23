"""AI-assisted host arithmetic regression; not a native MediaPlayer GUI test."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path


class ControllerFrameDurationTest(unittest.TestCase):
    def test_positive_short_clips(self):
        root = Path(__file__).resolve().parents[3]
        source = (root / 'src/apps/mediaplayer/Controller.cpp').read_text()
        method = re.search(r'int64\nController::_FrameDuration\(\) const\n\{.*?\n\}', source, re.S)
        self.assertIsNotNone(method)
        code = '''#include <cstdint>
#include <cstdio>
using int64 = int64_t;
struct Controller { int64 fDuration; float fVideoFrameRate; int64 _FrameDuration() const; };
''' + method.group() + '''
int main() {
    struct Case { int64 us; float rate; int64 want; };
    Case cases[] = {{0,25,0}, {33333,25,1}, {33333,30,1}, {1,25,1},
        {40000,25,1}, {5000000,30,150}, {1000000,25,25}};
    for (auto c : cases) {
        auto got = Controller{c.us,c.rate}._FrameDuration();
        if (got != c.want) {
            fprintf(stderr, "%lld us / %.0f fps: got %lld expected %lld\\n",
                (long long)c.us, c.rate, (long long)got, (long long)c.want);
            return 1;
        }
    }
    return 0;
}
'''
        with tempfile.TemporaryDirectory() as folder:
            src = Path(folder) / 'duration.cpp'
            exe = Path(folder) / 'duration'
            src.write_text(code)
            subprocess.run(['c++', '-std=c++11', str(src), '-o', str(exe)], check=True)
            subprocess.run([str(exe)], check=True)
