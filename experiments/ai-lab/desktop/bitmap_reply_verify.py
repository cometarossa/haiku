"""Independent expected wire values and read-only initial-memory verification."""
import csv
import io


def verify_reply(data, mode, treatment):
    if mode not in ("lab", "ordinary") or treatment not in ("off", "warm", "single", "quiet"):
        raise ValueError("invalid probe treatment")
    expected = {"off": 1, "warm": 1, "single": 9, "quiet": 25}[treatment] if mode == "lab" else 1
    checked = 262144 if mode == "lab" and treatment != "off" else 0
    rows = list(csv.reader(io.StringIO(data)))
    if len(rows) != 1 or len(rows[0]) != 5:
        raise ValueError("invalid reply record")
    if tuple(map(int, rows[0])) != (expected, expected, checked, 0, 0):
        raise ValueError("unexpected reply or initial bytes")
    return {"flags": expected, "checked": checked}
