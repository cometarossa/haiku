"""Validate each GOP independently; no cross-encode pixel equality claim."""
import json
from pathlib import Path
from v21_decode_report import frames,threads,REV

HASHES={120:"e21d1d21f4dd5793c33afad38adf8a43fb7cbeefa118ab4b2b51f551b632a62f",
        15:"ce435bd5c1ead746e3c3325d4ed4857c08aaabd4426d9a0b935384741d31df27"}
ORDER=(120,15,15,120)
TAGS=tuple(f"{i:02d}-gop-{g}" for i,g in enumerate(ORDER))

def validate(root):
    if (root/"done.txt").read_text().strip()!="0" or "ai_"+REV not in (root/"revision.txt").read_text():
        raise ValueError("wrong revision or incomplete")
    manifest=(root/"input-sha256.txt").read_text().splitlines()
    for g,d in HASHES.items():
        if f"{d}  gop-{g}.mp4" not in manifest:
            raise ValueError("wrong fixture")
    previous=0
    baseline={}
    rows=[]
    for tag,g in zip(TAGS,ORDER):
        def read(ext):
            return (root/(tag+"."+ext)).read_text()
        if read("exit").strip()!="0":raise ValueError("decode failed")
        data=frames(read("stdout"),3600)
        if g in baseline and data!=baseline[g]:
            raise ValueError("same-file pixel or timestamp regression")
        baseline[g]=data
        start,stop=int(read("start")),int(read("stop"))
        if not 0<=previous<start<stop:raise ValueError("clock")
        previous=stop
        rows.append(dict(tag=tag,gop=g,frames=len(data[0]),summary=data[1],elapsed_us=stop-start,
                         threads=threads(read("stderr"),"on")))
    return dict(valid=True,rows=rows,within_fixture_identical=True,
                cross_fixture_pixel_equality_required=False)

if __name__=="__main__":
    import sys
    print(json.dumps(validate(Path(sys.argv[1])),indent=2))
