"""Explicit five-phase client setup diagnostic; all durations are wall time."""
import csv
import io

from bitmap_warm_smoke import verify_client

PHASES = ("constructor_us", "lock_us", "white_scan_us", "attach_us", "initial_sync_us")


def verify_phases(data, mode, workers, batch):
    rows = list(csv.reader(io.StringIO(data)))
    if len(rows) != workers or any(len(row) != 18 for row in rows):
        raise ValueError("incorrect phase row shape")
    legacy = io.StringIO()
    csv.writer(legacy).writerows(row[:13] for row in rows)
    result = verify_client(legacy.getvalue(), mode, workers, batch)
    phases = []
    for row in rows:
        times = list(map(int, row[13:]))
        if any(t < 0 for t in times) or sum(times) != int(row[10]):
            raise ValueError("phase times do not sum to setup duration")
        phases.append(dict(worker=int(row[3]), **dict(zip(PHASES, times))))
    # Preserve per-worker phase attribution. Maxima from different workers
    # must not be added or treated as a single critical path.
    return result, sorted(phases, key=lambda r: r["worker"])


def slowest_setup_worker(phases):
    """Attribute the largest individual setup, not the global critical path."""
    if not phases:
        raise ValueError("missing workers")
    return max(phases, key=lambda r: (sum(r[k] for k in PHASES), -r["worker"]))


def paired_phase_deltas(block):
    """Within a three-treatment block, use the slowest setup in each run."""
    states = {r["flag"]: r for r in block}
    if len(block) != 3 or set(states) != {"off", "warm", "single"}:
        raise ValueError("incomplete treatment block")
    if len({(r["mode"], r["surfaces"]) for r in block}) != 1:
        raise ValueError("mixed topology")
    selected = {s: slowest_setup_worker(r["phases"]) for s, r in states.items()}
    for state in ("warm", "single"):
        diffs = {k: selected[state][k] - selected["off"][k] for k in PHASES}
        total = sum(diffs.values())
        if total != states[state]["max_setup_us"] - states["off"]["max_setup_us"]:
            raise ValueError("inconsistent maximum setup attribution")
        yield dict(mode=states[state]["mode"], surfaces=states[state]["surfaces"],
                   treatment=state, worker=selected[state]["worker"],
                   reference_worker=selected["off"]["worker"],
                   setup_delta_us=total, **{k.replace("_us", "_delta_us"): v for k, v in diffs.items()},
                   pre_render_delta_us=(states[state]["lifecycle_us"] - states[state]["render_us"]
                                        - states["off"]["lifecycle_us"] + states["off"]["render_us"]))
