"""Compile actual thread-count policy with the host compiler."""
import subprocess
import tempfile
import unittest
from pathlib import Path


class VideoThreadPolicyTest(unittest.TestCase):
    def test_policy(self):
        root=Path(__file__).resolve().parents[3]
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            (p/"test.cpp").write_text(r'''
#include <cassert>
#include "LabVideoThreadPolicy.h"
int main(){
    assert(LabVideoThreadCount(4,false,true,320,180)==4);
    assert(LabVideoThreadCount(4,true,true,320,180)==1);
    assert(LabVideoThreadCount(4,true,true,640,480)==1);
    assert(LabVideoThreadCount(4,true,true,641,480)==4);
    assert(LabVideoThreadCount(4,true,true,640,481)==4);
    assert(LabVideoThreadCount(4,true,true,1280,720)==4);
    assert(LabVideoThreadCount(4,true,false,320,180)==4);
    assert(LabVideoThreadCount(4,true,true,0,180)==4);
    assert(LabVideoThreadCount(4,true,true,320,-1)==4);
    assert(LabVideoThreadCount(0,true,true,320,180)==0);
    assert(LabVideoThreadCount(1,true,true,320,180)==1);
    assert(LabVideoThreadCount(64,true,true,320,180)==1);
}
''')
            subprocess.run(["c++","-std=c++11","-Wall","-Wextra","-Werror","-I",str(root/"src/add-ons/media/plugins/ffmpeg"),str(p/"test.cpp"),"-o",str(p/"test")],check=True)
            subprocess.run([str(p/"test")],check=True)
