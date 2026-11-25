#!/usr/bin/env python3
"""Strict validation of V15 per-lifetime counters; not a display FPS meter."""
import argparse
import json
import re
from pathlib import Path

FIELDS = {
    "PRODUCER": "thread lock_timeouts late attempts no_buffer fills fill_timeouts fill_errors end_buffers suppressed sent send_errors wait_us fill_us max_fill_us last_send_error".split(),
    "CONSUMER": "received inactive late target_calls no_target copy_bytes copy_us target_us first_target_us".split(),
}


def parse(text):
    result = {key: [] for key in FIELDS}
    for line in text.splitlines():
        if "LAB_MEDIA_PRODUCER" not in line and "LAB_MEDIA_CONSUMER" not in line:
            continue
        match = re.fullmatch(r"LAB_MEDIA_(PRODUCER|CONSUMER) (.*)", line)
        if not match:
            raise ValueError("interleaved or malformed diagnostic record")
        kind, raw = match.groups()
        pairs = [re.fullmatch(r"([a-z_]+)=(-?[0-9]+)", field) for field in raw.split()]
        if any(m is None for m in pairs):
            raise ValueError("malformed field")
        if [m.group(1) for m in pairs] != FIELDS[kind]:
            raise ValueError("missing, repeated, or unexpected field")
        row = {m.group(1): int(m.group(2)) for m in pairs}
        if any(v < 0 for k, v in row.items() if k != "last_send_error"):
            raise ValueError("negative counter")
        if kind == "PRODUCER":
            if row["attempts"] != row["no_buffer"] + row["fills"]:
                raise ValueError("request conservation failure")
            if row["fills"] != row["suppressed"] + row["sent"] + row["send_errors"]:
                raise ValueError("fill conservation failure")
            if row["fill_timeouts"] + row["fill_errors"] + row["end_buffers"] > row["fills"]:
                raise ValueError("fill outcome overflow")
            if row["max_fill_us"] > row["fill_us"]:
                raise ValueError("invalid max fill time")
            if bool(row["send_errors"]) != bool(row["last_send_error"]):
                raise ValueError("last error inconsistent")
        else:
            if row["received"] != sum(row[k] for k in ("inactive", "late", "target_calls", "no_target")):
                raise ValueError("consumer conservation failure")
            if bool(row["target_calls"]) != bool(row["first_target_us"]):
                raise ValueError("first target inconsistent")
        result[kind].append(row)
    return result


def summarize(result, enabled=True):
    if not enabled:
        if any(result.values()):
            raise ValueError("unexpected stats with marker OFF")
        return {}
    if not all(result.values()):
        raise ValueError("missing producer or consumer summaries")
    if not sum(r["sent"] for r in result["PRODUCER"]) or not sum(r["target_calls"] for r in result["CONSUMER"]):
        raise ValueError("no successful video activity")
    out = {}
    for kind, rows in result.items():
        aggregate = {"records": len(rows)}
        for key in FIELDS[kind]:
            if key in ("thread", "last_send_error", "first_target_us"):
                continue
            values = [r[key] for r in rows]
            aggregate[key] = max(values) if key == "max_fill_us" else sum(values)
        out[kind.lower()] = aggregate
    # Do not equate producer sent and consumer handled: shutdown, queued
    # events, and separate lifetimes prevent exact cross-stage accounting.
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("log", type=Path)
    p.add_argument("--off", action="store_true")
    args = p.parse_args()
    print(json.dumps(summarize(parse(args.log.read_text()), not args.off), indent=2))


if __name__ == "__main__":
    main()
