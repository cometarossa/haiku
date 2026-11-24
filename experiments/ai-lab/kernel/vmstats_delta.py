#!/usr/bin/env python3
"""Validate cumulative V6/V7a/V7b VM diagnostic snapshots and emit CSV deltas.

AI-assisted independent research fork.
Deltas are system-wide observation windows, not isolated workload timings.
An enable/disable transition alone does not establish a matched experiment.
"""
import argparse
import csv
import re
import sys
from pathlib import Path

FIELDS = {
    "LAB_VM": ("enabled", "locks", "lock_wait_us", "empty_flushes",
               "flushes", "flush_us", "invalid_pages", "remote_candidates"),
    "LAB_VM_WAIT": ("outer", "wait_us", "ge50us", "ge1ms"),
    "LAB_VM_HOLD": ("samples", "hold_us", "ge50us", "ge1ms"),
    "LAB_MUTEX": ("enabled", "samples", "invalid"),
    "LAB_MUTEX_QUEUE": ("us", "ge50us", "ge1ms"),
    "LAB_MUTEX_RESUME": ("us", "ge50us", "ge1ms"),
}
PAT = re.compile(r"^\s*(LAB_VM(?:_WAIT|_HOLD)?|LAB_MUTEX(?:_QUEUE|_RESUME)?)\s+(.*)$")

def snapshots(lines):
    current = None
    for line in lines:
        match = PAT.match(line)
        if not match:
            continue
        group, body = match.groups()
        values = dict((k, int(v)) for k, v in re.findall(r"(\w+)=(\d+)", body))
        if group == "LAB_VM" and "enabled" in values:
            if current is not None:
                yield validate(current)
            current = {}
        if current is None:
            raise ValueError("counter line before snapshot")
        for k, v in values.items():
            if k not in FIELDS[group]:
                raise ValueError("unknown field: " + k)
            key = group + "." + k
            if key in current:
                raise ValueError("duplicate field: " + key)
            current[key] = v
    if current is not None:
        yield validate(current)

def validate(s):
    groups = {key.split(".")[0] for key in s}
    if groups not in ({"LAB_VM"}, {"LAB_VM", "LAB_VM_WAIT", "LAB_VM_HOLD"}, set(FIELDS)):
        raise ValueError("incomplete diagnostic snapshot")
    for group in groups:
        for field in FIELDS[group]:
            if group + "." + field not in s:
                raise ValueError("missing field: " + group + "." + field)
    if s["LAB_VM.enabled"] not in (0, 1):
        raise ValueError("invalid sampling flag")
    if "LAB_MUTEX.enabled" in s and s["LAB_MUTEX.enabled"] not in (0, 1):
        raise ValueError("invalid mutex sampling flag")
    return s

def deltas(rows):
    for n, (a, b) in enumerate(zip(rows, rows[1:]), 1):
        if a.keys() != b.keys():
            raise ValueError("snapshot schema changed")
        d = {k: b[k] - a[k] for k in a if not k.endswith(".enabled")}
        if min(d.values()) < 0:
            raise ValueError("counter decreased; possible reboot/reset")
        for group, total in (("LAB_VM_WAIT", "outer"), ("LAB_VM_HOLD", "samples")):
            if group + "." + total in d:
                if not d[group + ".ge1ms"] <= d[group + ".ge50us"] <= d[group + "." + total]:
                    raise ValueError("inconsistent delta histogram")
        mutex_flags = {}
        if "LAB_MUTEX.samples" in d:
            if d["LAB_MUTEX.invalid"]:
                raise ValueError("invalid mutex timestamp in window")
            for group in ("LAB_MUTEX_QUEUE", "LAB_MUTEX_RESUME"):
                if not d[group + ".ge1ms"] <= d[group + ".ge50us"] <= d["LAB_MUTEX.samples"]:
                    raise ValueError("inconsistent mutex delta histogram")
            mutex_flags = {"mutex_enabled_start": a["LAB_MUTEX.enabled"],
                           "mutex_enabled_end": b["LAB_MUTEX.enabled"]}
        yield {"window": n, "enabled_start": a["LAB_VM.enabled"],
               "enabled_end": b["LAB_VM.enabled"], **mutex_flags, **d}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("log", type=Path)
    args = p.parse_args()
    try:
        rows = list(snapshots(args.log.read_text(errors="replace").splitlines()))
        if len(rows) < 2:
            raise ValueError("need two complete snapshots")
        out = list(deltas(rows))
        writer = csv.DictWriter(sys.stdout, fieldnames=list(out[0]))
        writer.writeheader()
        writer.writerows(out)
    except (OSError, ValueError) as exc:
        p.exit(1, str(exc) + "\n")

if __name__ == "__main__":
    main()
