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
