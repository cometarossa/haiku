#!/usr/bin/env python3
"""Staged native persistent-query test; requires confirmed V18 Terminal."""
import hashlib
import importlib
import json
import socket
import subprocess
import sys
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from threading import Thread
from v16_catchup_runner import HOME, MEDIA, LAB, sample_host
from window_probe_report import analyze

REV = "fb8c2e41"
SPECS = (4, 8, 16)


def deferred_load_script(script, sixteen=False):
    """Generate a balanced, fixed-duration same-image comparison."""
    changes = [
        (b'v18-probe-load-ram', b'v19-deferred-load-16-ram' if sixteen else b'v19-deferred-load-ram', 2),
        (b'for spec in 4-on 8-on 16-on;', b'for spec in 16-off 16-on 16-on 16-off;' if sixteen else b'for spec in 4-off 4-on 4-on 4-off 8-off 8-on 8-on 8-off;', 1),
        (b'catchup=/boot/home/config/settings/haiku-lab-video-view-stats', b'catchup=/boot/home/config/settings/haiku-lab-video-deferred\nview=/boot/home/config/settings/haiku-lab-video-view-stats', 1),
        (b'for m in "$stats" "$preflight" "$catchup"', b'for m in "$stats" "$preflight" "$catchup" "$view"', 2),
        (b's=0;p=0;c=0', b's=0;p=0;c=0;v=0', 1),
        (b'cleanup() {', b'cleanup() {\n if test "$v" = 1; then rm -f "$view"; v=0; fi', 1),
        (b'(set -C; : > "$stats"); s=1', b'(set -C; : > "$stats"); s=1\n(set -C; : > "$view"); v=1', 1),
        (b' system_time > "$tag.stop"', b' # Hold the observation window at 20 s from last Play reply.\n while test "$(( $(system_time) - $(cat "$tag.play") ))" -lt 20000000; do sleep .1; done\n system_time > "$tag.stop"', 1),
    ]
    for old,new,count in changes:
        if script.count(old)!=count:
            raise ValueError("Unexpected source script anchor: "+repr(old))
        script=script.replace(old,new)
    return script


def v20_diagnostic_script(script, streams):
    if streams not in (4,8,16):
        raise ValueError("Unsupported V20 load")
    script=deferred_load_script(script,False)
    order=" ".join(f"{streams}-{state}" for state in ("off","on","on","off")).encode()
    changes=[
        (b'v19-deferred-load-ram', f'v20-diagnostic-{streams}-ram'.encode(), 2),
        (b'for spec in 4-off 4-on 4-on 4-off 8-off 8-on 8-on 8-off;', b'for spec in '+order+b';', 1),
        (b'view=/boot/home/config/settings/haiku-lab-video-view-stats', b'view=/boot/home/config/settings/haiku-lab-video-view-stats\ntiming=/boot/home/config/settings/haiku-lab-video-deferred-timing\nproxy=/boot/home/config/settings/haiku-lab-video-proxy-stats', 1),
        (b'"$catchup" "$view"', b'"$catchup" "$view" "$timing" "$proxy"', 2),
        (b's=0;p=0;c=0;v=0', b's=0;p=0;c=0;v=0;own_timing=0;own_proxy=0', 1),
        (b'cleanup() {', b'cleanup() {\n if test "$own_timing" = 1; then rm -f "$timing"; own_timing=0; fi\n if test "$own_proxy" = 1; then rm -f "$proxy"; own_proxy=0; fi', 1),
        (b'(set -C; : > "$view"); v=1', b'(set -C; : > "$view"); v=1\n(set -C; : > "$timing"); own_timing=1\n(set -C; : > "$proxy"); own_proxy=1', 1),
    ]
    for old,new,count in changes:
        if script.count(old)!=count:
            raise ValueError("Unexpected V20 script anchor: "+repr(old))
        script=script.replace(old,new)
    script=script.replace(b'test ! -e "$m" && test ! -L "$m"', b'if test -e "$m" || test -L "$m"; then echo "Unexpected marker: $m" >&2; exit 7; fi')
    script=script.replace(b'test ! -e "$catchup" && test ! -L "$catchup"', b'if test -e "$catchup" || test -L "$catchup"; then exit 7; fi')
    return script


def v21_lifecycle_script(script):
    changes=[
        (b'v19-deferred-smoke',b'v21-thread-smoke',2),
        (b'deferred="$settings/haiku-lab-video-deferred"',b'deferred="$settings/haiku-lab-h264-single-thread"\nthreadstats="$settings/haiku-lab-video-thread-stats"',1),
        (b'"$view" "$deferred"',b'"$view" "$deferred" "$threadstats" "$settings/haiku-lab-video-deferred" "$settings/haiku-lab-video-deferred-timing" "$settings/haiku-lab-video-proxy-stats"',1),
        (b'test ! -e "$m" && test ! -L "$m"',b'if test -e "$m" || test -L "$m"; then echo "Unexpected marker $m" >&2; exit 7; fi',1),
        (b's=0;p=0;v=0;d=0',b's=0;p=0;v=0;d=0;own_threadstats=0',1),
        (b'cleanup() {',b'cleanup() {\n if test "$own_threadstats" = 1; then rm -f "$threadstats"; own_threadstats=0; fi',1),
        (b'(set -C; : > "$view"); v=1',b'(set -C; : > "$view"); v=1\n(set -C; : > "$threadstats"); own_threadstats=1',1),
    ]
    for old,new,count in changes:
        if script.count(old)!=count:
            raise ValueError("Unexpected lifecycle source anchor: "+repr(old))
        script=script.replace(old,new)
    return script


def v21_load_script(script, streams):
    script=v20_diagnostic_script(script,streams)
    changes=[
        (f'v20-diagnostic-{streams}-ram'.encode(), f'v21-thread-{streams}-ram'.encode(), 2),
        (b'catchup=/boot/home/config/settings/haiku-lab-video-deferred\n', b'catchup=/boot/home/config/settings/haiku-lab-h264-single-thread\nthreadstats=/boot/home/config/settings/haiku-lab-video-thread-stats\ndeferred=/boot/home/config/settings/haiku-lab-video-deferred\n',1),
        (b'"$catchup" "$view" "$timing" "$proxy"',b'"$catchup" "$view" "$timing" "$proxy" "$threadstats" "$deferred"',2),
        (b'own_timing=0;own_proxy=0',b'own_timing=0;own_proxy=0;own_threadstats=0',1),
        (b'cleanup() {',b'cleanup() {\n if test "$own_threadstats" = 1; then rm -f "$threadstats"; own_threadstats=0; fi',1),
        (b'(set -C; : > "$timing"); own_timing=1',b'(set -C; : > "$threadstats"); own_threadstats=1',1),
    ]
    for old,new,count in changes:
        if script.count(old)!=count:
            raise ValueError("Unexpected V21 source anchor: "+repr(old))
        script=script.replace(old,new)
    return script


def v21_combined_script(script, streams):
    # Hold single-thread decoding fixed; toggle deferred rendering only.
    script=v21_load_script(script,streams)
    changes=[
        (f'v21-thread-{streams}-ram'.encode(),f'v21-combined-{streams}-ram'.encode(),2),
        (b'catchup=/boot/home/config/settings/haiku-lab-h264-single-thread',b'catchup=/boot/home/config/settings/haiku-lab-video-deferred',1),
        (b'deferred=/boot/home/config/settings/haiku-lab-video-deferred',b'single=/boot/home/config/settings/haiku-lab-h264-single-thread',1),
        (b'"$threadstats" "$deferred"',b'"$threadstats" "$single"',2),
        (b'own_threadstats=0\ncleanup()',b'own_threadstats=0;own_single=0\ncleanup()',1),
        (b'cleanup() {',b'cleanup() {\n if test "$own_single" = 1; then rm -f "$single"; own_single=0; fi',1),
        (b'(set -C; : > "$threadstats"); own_threadstats=1',b'(set -C; : > "$threadstats"); own_threadstats=1\n(set -C; : > "$single"); own_single=1\n(set -C; : > "$timing"); own_timing=1',1),
    ]
    for old,new,count in changes:
        if script.count(old)!=count:
            raise ValueError("Unexpected combined source anchor: "+repr(old))
        script=script.replace(old,new)
    return script


def v22_gop_script(script, streams):
    # OFF = GOP 120, ON = GOP 15; both use the same decoder/renderer.
    script=v21_combined_script(script,streams)
    changes=[
        (f'v21-combined-{streams}-ram'.encode(),f'v22-gop-{streams}-ram'.encode(),2),
        (b'for f in stream-a.mp4 media-window-probe SHA256SUMS;',b'for f in gop-120.mp4 gop-15.mp4 media-window-probe SHA256SUMS;',1),
        (b'(set -C; : > "$timing"); own_timing=1\n',b'',1),
        (b'if test "$st" = on; then (set -C; : > "$catchup"); c=1; fi',b'if test "$st" = on; then fixture=gop-15.mp4; else fixture=gop-120.mp4; fi',1),
        (b'cp stream-a.mp4 "$tag-$i.mp4"; cmp stream-a.mp4 "$tag-$i.mp4"',b'cp "$fixture" "$tag-$i.mp4"; cmp "$fixture" "$tag-$i.mp4"',1),
    ]
    for old,new,count in changes:
        if script.count(old)!=count:
            raise ValueError("Unexpected GOP source anchor: "+repr(old))
        script=script.replace(old,new)
    return script


def record_teardown_clocks(script):
    """Separate observation, quit RPC, and actual process exit."""
    changes=[
        (b' system_time > "$tag.quit-time"\n hey "$app" quit || true',b' system_time > "$tag.quit-time"\n curl -fsS -T "$tag.quit-time" "$base/$tag.quit-time"\n hey "$app" quit || true\n system_time > "$tag.quit-return"',1),
        (b'for ext in start quit-time windows positions stdout stderr exit;',b'system_time > "$tag.exit-time"\n for ext in start quit-return exit-time windows positions stdout stderr exit;',1),
    ]
    for old,new,count in changes:
        if script.count(old)!=count:
            raise ValueError("Unexpected teardown anchor: "+repr(old))
        script=script.replace(old,new)
    return script


def observation_script(script, mode, streams=4):
    if mode not in ("off","on") or streams not in (4,8,16):
        raise ValueError("invalid observation mode or streams")
    changes=[
        (f'v21-combined-{streams}-ram'.encode(),f'v22-observation-{mode}-{streams}-ram'.encode(),2),
        (b'proxy=/boot/home/config/settings/haiku-lab-video-proxy-stats',b'proxy=/boot/home/config/settings/haiku-lab-video-proxy-stats\nobservation=/boot/home/config/settings/haiku-lab-video-observation\nfilltiming=/boot/home/config/settings/haiku-lab-video-fill-timing',1),
        (b'"$threadstats" "$single"',b'"$threadstats" "$single" "$observation" "$filltiming"',2),
        (b'own_single=0\ncleanup()',b'own_single=0;own_observation=0;own_filltiming=0\ncleanup()',1),
        (b'cleanup() {',b'cleanup() {\n if test "$own_observation" = 1; then rm -f "$observation"; own_observation=0; fi\n if test "$own_filltiming" = 1; then rm -f "$filltiming"; own_filltiming=0; fi',1),
    ]
    if mode=="on":
        changes.append((b'(set -C; : > "$single"); own_single=1',b'(set -C; : > "$single"); own_single=1\n(set -C; : > "$observation"); own_observation=1\n(set -C; : > "$filltiming"); own_filltiming=1',1))
    for old,new,count in changes:
        if script.count(old)!=count:
            raise ValueError("Unexpected observation anchor: "+repr(old))
        script=script.replace(old,new)
    return script


def run(root, queues=False, deferred_smoke=False, deferred_load=False, sixteen=False, smoke_evidence=None, v20_streams=None, v20_evidence=None, v21_smoke=False, v21_decode_evidence=None, v21_streams=None, v21_evidence=None, combined=False, combined_evidence=None, gop=False, gop_decode_evidence=None, gop_evidence=None, observation=None, observation_evidence=None, scaling_evidence=None, scaling_prior=None, appserver_profile=None):
    if sum((queues,deferred_smoke,deferred_load,v20_streams is not None,v21_smoke,v21_streams is not None))>1 or (sixteen and not deferred_load):
        raise ValueError("Select one campaign")
    if observation is not None and (not combined or v21_streams not in (4,8,16)):
        raise ValueError("Observation requires combined campaign")
    if observation is not None and v21_streams>4:
        from v22_observation_smoke_report import analyze as analyze_observation
        if observation!="on" or observation_evidence is None:
            raise ValueError("Active observation and preceding native evidence required")
        prior=analyze_observation(observation_evidence,"on",v21_streams//2)
        if not (prior["complete"] and prior["all_diagnostic_valid"] and prior["all_playback_valid"]):
            raise ValueError("Prior observation gate not met")
    if gop and (combined or v21_streams is None):
        raise ValueError("GOP requires V21 streams without combined treatment")
    if combined and v21_streams is None:
        raise ValueError("Combined treatment requires V21 streams")
    revision = "067ee57e" if deferred_smoke or deferred_load else REV
    specs = ((1,"off"),(1,"on")) if deferred_smoke else tuple((n,"on") for n in ((8,) if queues else SPECS))
    if deferred_load:
        from v19_deferred_report import validate
        if smoke_evidence is None:
            raise ValueError("A validated V19 lifecycle smoke evidence root is required")
        validate(smoke_evidence)
        specs = tuple((n,state) for n in ((16,) if sixteen else (4,8)) for state in ("off","on","on","off"))
    if v20_streams is not None:
        from v19_deferred_report import validate
        if smoke_evidence is None:
            raise ValueError("V19 lifecycle smoke evidence required")
        validate(smoke_evidence)
        if v20_streams not in (4,8,16):
            raise ValueError("Unsupported V20 load")
        if v20_streams > 4:
            from v20_diagnostic_report import report
            if v20_evidence is None:
                raise ValueError("Validated V20 four-stream campaign required")
            gate=report(v20_evidence,4)
            if not gate["complete"] or not gate["all_diagnostic_valid"] or not gate["all_playback_valid"]:
                raise ValueError("V20 four-stream gate not met")
        revision="11904750"
        specs=tuple((v20_streams,state) for state in ("off","on","on","off"))
    if v21_smoke:
        from v21_decode_report import validate_repeat
        if v21_decode_evidence is None or not validate_repeat(v21_decode_evidence)["identical"]:
            raise ValueError("V21 balanced decode correctness gate required")
        revision="2f9d27bf"
        specs=((1,"off"),(1,"on"))
    if v21_streams is not None:
        from v19_deferred_report import validate
        from v21_decode_report import validate_repeat
        if v21_decode_evidence is None or not validate_repeat(v21_decode_evidence)["identical"]:
            raise ValueError("V21 balanced decode correctness gate required")
        if smoke_evidence is None:
            raise ValueError("V21 lifecycle gate required")
        validate(smoke_evidence,"2f9d27bf",thread_policy=True)
        if v21_streams not in (4,8,16):
            raise ValueError("Unsupported V21 load")
        if v21_streams > 4:
            from v21_load_report import report
            if v21_evidence is None:
                raise ValueError("V21 four-stream gate required")
            gate=report(v21_evidence,4)
            if not gate["complete"] or not gate["all_diagnostic_valid"] or not gate["all_playback_valid"]:
                raise ValueError("V21 four-stream gate not met")
        if combined and v21_streams>4:
            from v21_load_report import report
            if combined_evidence is None:
                raise ValueError("Combined four-stream gate required")
            gate=report(combined_evidence,4,combined=True)
            if not gate["all_diagnostic_valid"] or not gate["all_playback_valid"]:
                raise ValueError("Combined four-stream gate not met")
        revision="2f9d27bf"
        specs=tuple((v21_streams,state) for state in ("off","on","on","off"))
    if gop:
        from v22_gop_decode_report import validate as validate_gop
        if gop_decode_evidence is None or not validate_gop(gop_decode_evidence)["valid"]:
            raise ValueError("GOP native decode gate required")
        if v21_streams>4:
            from v21_load_report import report
            if gop_evidence is None:
                raise ValueError("GOP four-stream gate required")
            gate=report(gop_evidence,4,gop=True)
            if not gate["all_diagnostic_valid"] or not gate["all_playback_valid"]:
                raise ValueError("GOP four-stream gate not met")
    if observation is not None:
        revision="4ae8e7ea"
    if scaling_evidence is not None:
        from v23_scaling_campaign import SHA,validate_smoke,report as scaling_report
        if observation!="on" or v21_streams not in (4,8,16) or not combined or observation_evidence is None:
            raise ValueError("Scaling requires V22 four-stream observation and native evidence")
        from v22_observation_smoke_report import analyze as analyze_observation
        gate=analyze_observation(observation_evidence,"on",4 if v21_streams==4 else v21_streams//2)
        if not gate["all_diagnostic_valid"] or not gate["all_playback_valid"]:
            raise ValueError("V22 observation gate failed")
        if v21_streams>4:
            if scaling_prior is None:raise ValueError("preceding native scaling evidence required")
            prior=scaling_report(scaling_prior,scaling_evidence,v21_streams//2)
            if not (prior["complete"] and prior["all_diagnostic_valid"] and prior["all_playback_valid"]):
                raise ValueError("preceding scaling gate failed")
        settings_sha=validate_smoke(scaling_evidence)["sha256"]
    if appserver_profile is not None:
        from v23_appserver_profile import REV as server_revision
        if observation!="on" or v21_streams!=4 or not combined or scaling_evidence is not None or observation_evidence is None:
            raise ValueError("Appserver smoke requires native four-stream observation evidence")
        from v22_observation_smoke_report import analyze as analyze_observation
        gate=analyze_observation(observation_evidence,"on",4)
        if not gate["all_diagnostic_valid"] or not gate["all_playback_valid"]:
            raise ValueError("V22 observation gate failed")
        revision=server_revision
    initial = sample_host(revision)
    pids = {g["pid"] for g in initial["guests"]}
    downloads = {}
    for folder, name, alias in (
        ("v17-long-sd", "stream-long-sd.mp4", "stream-a.mp4"),
        ("window-probe-d9c8b5b9", "media-window-probe", "media-window-probe"),
    ):
        src = HOME/"guest-files"/folder
        b = (src/name).read_bytes()
        if hashlib.sha256(b).hexdigest() != (src/"SHA256SUMS").read_text().split()[0]:
            raise ValueError("input checksum mismatch")
        downloads[alias] = b
    if gop:
        from v22_gop_decode_report import HASHES
        del downloads["stream-a.mp4"]
        for g,expected in HASHES.items():
            name=f"gop-{g}.mp4"
            data=(HOME/"guest-files"/"v22-gop"/name).read_bytes()
            if hashlib.sha256(data).hexdigest()!=expected:
                raise ValueError("GOP fixture checksum")
            downloads[name]=data
    if scaling_evidence is not None:
        data=(HOME/"guest-files/scaling-helper-83f428d4/scaling-settings").read_bytes()
        if hashlib.sha256(data).hexdigest()!=SHA:raise ValueError("scaling helper checksum")
        downloads["scaling-settings"]=data
    downloads["SHA256SUMS"] = "".join(
        f"{hashlib.sha256(b).hexdigest()}  {n}\n" for n,b in downloads.items()).encode()
    script = (MEDIA/"v18-probe-load-guest.sh").read_bytes()
    if queues:
        script=(MEDIA/"v18-queue-load-guest.sh").read_bytes()
    if deferred_smoke:
        script=(MEDIA/"v19-deferred-smoke-guest.sh").read_bytes()
    if deferred_load:
        script=deferred_load_script(script,sixteen)
    if v20_streams is not None:
        script=v20_diagnostic_script(script,v20_streams)
    if v21_smoke:
        script=v21_lifecycle_script((MEDIA/"v19-deferred-smoke-guest.sh").read_bytes())
    if v21_streams is not None:
        script=v21_combined_script(script,v21_streams) if combined else v21_load_script(script,v21_streams)
    if gop:
        script=v22_gop_script((MEDIA/"v18-probe-load-guest.sh").read_bytes(),v21_streams)
    if v21_streams is not None:
        script=record_teardown_clocks(script)
    if observation is not None:
        script=observation_script(script,observation,v21_streams)
    if scaling_evidence is not None:
        from v23_scaling_campaign import scaling_script
        script=scaling_script(script,settings_sha,v21_streams)
    if appserver_profile is not None:
        from v23_appserver_profile import profile_script
        script=profile_script(script,appserver_profile,v21_streams)
    subprocess.run(["sh","-n"],input=script,check=True)
    downloads["run.sh"] = script
    allowed = {"revision.txt","done.txt"} | {
        f"{i:02d}-n{n}-{state}.{ext}" for i,(n,state) in enumerate(specs)
        for ext in ("dispatch","play","stop","map","probe","probe-stderr","probe-exit",
                    "start","quit-time","quit-return","exit-time","windows","positions","stdout","stderr","exit","lifecycle","pause")}
    if scaling_evidence is not None:
        allowed|={"settings-restored.txt"}|{f"{i:02d}-n{n}-{state}.{ext}" for i,(n,state) in enumerate(specs) for ext in ("scaling-before","scaling-after")}
    if queues:
        allowed |= {"teams.txt","00-n8-on.teams","00-n8-on.ports"} | {
            f"00-n8-on.port-{i:02d}" for i in range(1,11)}
    root.mkdir()
    (root/"run.sh").write_bytes(script)
    (root/"input-sha256.txt").write_bytes(downloads["SHA256SUMS"])
    (root/"runner-source.py").write_bytes(Path(__file__).read_bytes())
    (root/"host-start.json").write_text(json.dumps(initial,indent=2)+"\n")

    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            data = downloads.get(self.path[1:])
            if data is None:
                self.send_error(404); return
            self.send_response(200)
            self.send_header("Content-Length",str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_PUT(self):
            name = self.path[1:]
            try:
                length = int(self.headers.get("Content-Length","-1"))
            except ValueError:
                self.send_error(400); return
            limit = 32000000 if name.endswith((".stdout",".stderr")) else 2000000
            if name not in allowed or not 0 <= length <= limit or (root/name).exists():
                self.send_error(400); return
            data = self.rfile.read(length)
            if len(data) != length:
                self.send_error(400); return
            temp = root/(name+".partial")
            temp.write_bytes(data)
            temp.rename(root/name)
            self.send_response(201); self.end_headers()

    serial=None
    if appserver_profile is not None:
        serial=HOME/"ai-images"/f"run-local-{revision}"/"haiku-ai-regular-serial.log"
        if not serial.is_file():raise ValueError("serial file missing")
        serial_stat=serial.stat()
        serial_offset=serial_stat.st_size
    server = HTTPServer(("127.0.0.1",8901),H)
    t = Thread(target=server.serve_forever,daemon=True)
    t.start()
    try:
        cmd = [sys.executable,str(LAB/"guest-hmp.py"),"--local-id",revision,"type"]
        subprocess.run(cmd+["curl -fsS http://10.0.2.2:8901/run.sh -o load18.sh"],check=True,timeout=30)
        subprocess.run(cmd+["sh load18.sh"],check=True,timeout=30)
        sys.path.insert(0,str(LAB))
        h = importlib.import_module("guest-hmp")
        deadline = time.monotonic()+(1200 if deferred_load or v20_streams is not None or v21_streams is not None else 600)
        index=0
        while time.monotonic()<deadline:
            sample=sample_host(revision)
            if {g["pid"] for g in sample["guests"]} != pids:
                raise RuntimeError("VM inventory changed")
            with (root/"host-samples.jsonl").open("a") as f:
                f.write(json.dumps(sample)+"\n")
            ppm=root/f"frame-{index:03d}.ppm"
            with socket.socket(socket.AF_UNIX) as sock:
                sock.settimeout(8)
                sock.connect(str(HOME/"ai-images"/f"run-local-{revision}"/"haiku-ai-regular-monitor.sock"))
                h.receive_prompt(sock)
                h.exchange(sock,"screendump "+str(ppm))
            subprocess.run(["sips","-s","format","png",str(ppm),"--out",str(ppm.with_suffix(".png"))],check=True,stdout=subprocess.DEVNULL)
            ppm.unlink()
            index+=1
            if (root/"done.txt").exists():
                break
            time.sleep(4)
        else:
            raise TimeoutError("campaign incomplete; preserve guest and logs")
        if (root/"done.txt").read_text().strip()!="0" or "ai_"+revision not in (root/"revision.txt").read_text():
            raise ValueError("completion or revision invalid")
        rows=[]
        for i,(n,state) in enumerate(specs):
            tag=f"{i:02d}-n{n}-{state}"
            mapping=[int(l.split()[0]) for l in (root/(tag+".map")).read_text().splitlines()]
            if len(mapping)!=n:
                raise ValueError("window count")
            r=analyze((root/(tag+".probe")).read_text(),mapping)
            r.update(n=n,state=state,probe_exit=int((root/(tag+".probe-exit")).read_text()),
                     player_exit=int((root/(tag+".exit")).read_text()))
            rows.append(r)
        if v21_smoke:
            from v19_deferred_report import validate
            rows=validate(root,revision,thread_policy=True)
        if serial is not None:
            time.sleep(2)
            stat=serial.stat()
            if stat.st_ino!=serial_stat.st_ino or stat.st_size<serial_offset:
                raise ValueError("serial file replaced or truncated")
            with serial.open("rb") as f:
                f.seek(serial_offset)
                (root/"appserver-serial.log").write_bytes(f.read())
        (root/"summary.json").write_text(json.dumps(rows,indent=2)+"\n")
        print(json.dumps(rows,indent=2))
    finally:
        server.shutdown();server.server_close();t.join()
        if serial is not None and not (root/"appserver-serial.log").exists():
            stat=serial.stat()
            if stat.st_ino==serial_stat.st_ino and stat.st_size>=serial_offset:
                with serial.open("rb") as f:
                    f.seek(serial_offset)
                    (root/"appserver-serial.log").write_bytes(f.read())


if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("root",type=Path)
    p.add_argument("--queues",action="store_true")
    p.add_argument("--deferred-smoke",action="store_true")
    p.add_argument("--deferred-load",action="store_true")
    p.add_argument("--sixteen",action="store_true")
    p.add_argument("--smoke-evidence",type=Path)
    p.add_argument("--v20-streams",type=int,choices=(4,8,16))
    p.add_argument("--v20-evidence",type=Path)
    p.add_argument("--v21-smoke",action="store_true")
    p.add_argument("--v21-decode-evidence",type=Path)
    p.add_argument("--v21-streams",type=int,choices=(4,8,16))
    p.add_argument("--v21-evidence",type=Path)
    p.add_argument("--combined",action="store_true")
    p.add_argument("--combined-evidence",type=Path)
    p.add_argument("--gop",action="store_true")
    p.add_argument("--gop-decode-evidence",type=Path)
    p.add_argument("--gop-evidence",type=Path)
    p.add_argument("--observation",choices=("off","on"))
    p.add_argument("--observation-evidence",type=Path)
    p.add_argument("--scaling-evidence",type=Path)
    p.add_argument("--scaling-prior",type=Path)
    p.add_argument("--appserver-profile",choices=("off","on"))
    a=p.parse_args()
    run(a.root,a.queues,a.deferred_smoke,a.deferred_load,a.sixteen,a.smoke_evidence,a.v20_streams,a.v20_evidence,a.v21_smoke,a.v21_decode_evidence,a.v21_streams,a.v21_evidence,a.combined,a.combined_evidence,a.gop,a.gop_decode_evidence,a.gop_evidence,a.observation,a.observation_evidence,a.scaling_evidence,a.scaling_prior,a.appserver_profile)
