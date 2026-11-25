#!/usr/bin/env python3
"""AI-assisted independent Haiku research fork: validate V10 serial records."""
import argparse
import json
import re
from pathlib import Path

PHASES = {"window", "desktop_read", "desktop_write", "dispatch",
          "sync", "fill", "bitmap"}
ROW = re.compile(
    r"LAB_APPWIN team=(\d+) port=(\d+) phase=([a-z_]+)"
    r" n=(\d+) us=(\d+) max=(\d+) ge50=(\d+)")
END = re.compile(r"LAB_APPWIN_END team=(\d+) port=(\d+) normal=([01])")


def parse(text, expected_windows, expected_fills):
    windows = {}
    for line in text.splitlines():
        if not line.startswith("LAB_APPWIN"):
            continue
        row = ROW.fullmatch(line)
        end = END.fullmatch(line)
        if row:
            team, port, phase, *values = row.groups()
            key = (int(team), int(port))
            result = windows.setdefault(key, {})
            if phase not in PHASES or phase in result or "normal" in result:
                raise ValueError("unexpected or duplicate phase: " + line)
            n, total, maximum, slow = map(int, values)
            if (slow > n or maximum > total or total > n * maximum
                    or slow * 50 > total or bool(slow) != (maximum >= 50)
                    or (n and total > slow * maximum + (n-slow)*49)):
                raise ValueError("inconsistent timing: " + line)
            result[phase] = dict(n=n, us=total, max=maximum, ge50=slow)
        elif end:
            team, port, normal = map(int, end.groups())
            result = windows.get((team, port), {})
            if set(result) != PHASES or normal != 1:
                raise ValueError("incomplete or abnormal window: " + line)
            result["normal"] = normal
        else:
            raise ValueError("malformed profile row: " + line)
    if len(windows) != expected_windows:
        raise ValueError(f"expected {expected_windows} windows, got {len(windows)}")
    for result in windows.values():
        if set(result) != PHASES | {"normal"}:
            raise ValueError("missing completion record")
        for k in ("n", "us", "ge50"):
            if sum(result[p][k] for p in ("sync", "fill", "bitmap")) > result["dispatch"][k]:
                raise ValueError("dispatch subsets exceed total")
        if max(result[p]["max"] for p in ("sync", "fill", "bitmap")) > result["dispatch"]["max"]:
            raise ValueError("dispatch subset maximum exceeds total")
    if sum(w["fill"]["n"] for w in windows.values()) != expected_fills:
        raise ValueError("unexpected FillRect count")
    return [dict(team=team, port=port, **result)
            for (team, port), result in sorted(windows.items())]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("serial", type=Path)
    parser.add_argument("--windows", required=True, type=int)
    parser.add_argument("--fills", required=True, type=int)
    args = parser.parse_args()
    if min(args.windows, args.fills) < 0:
        parser.error("counts must be nonnegative")
    print(json.dumps(parse(args.serial.read_text(errors="replace"),
                           args.windows, args.fills), indent=2))


if __name__ == "__main__":
    main()
