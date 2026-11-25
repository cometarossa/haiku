#!/usr/bin/env python3
"""AI-assisted Haiku research-fork QEMU monitor client (macOS only).

Uses only known laboratory QEMU monitor UNIX sockets. The type command
simulates guest keyboard input, so use explicit targets and text.
"""
import argparse
import re
from pathlib import Path
import socket
import time


def receive_prompt(sock):
    # QEMU sends a banner and prompt in separate UNIX socket writes.
    # Read *all* of each reply, not just the first partial chunk.
    output = bytearray()
    for _ in range(150):
        chunk = sock.recv(8192)
        if not chunk:
            raise RuntimeError("QEMU monitor closed unexpectedly")
        output.extend(chunk)
        if output.endswith(b"(qemu) "):
            return output.decode("utf-8", errors="replace")
    raise RuntimeError("QEMU monitor prompt not received")


def exchange(sock, line):
    sock.sendall((line + "\n").encode("ascii"))
    reply = receive_prompt(sock)
    # HMP echoes individual typed command characters with ANSI cursor
    # controls. The useful command response begins after the CRLF.
    if "\r\n" in reply:
        reply = reply.split("\r\n", 1)[1]
    reply = reply.rsplit("(qemu) ", 1)[0].strip()
    if "Error:" in reply or "unknown command" in reply:
        raise RuntimeError("QEMU rejected command: " + reply[-250:])
    return reply


def keyboard(text):
    aliases = {
        " ": "spc", "/": "slash", ".": "dot", "-": "minus",
        "_": "shift-minus", ":": "shift-semicolon",
    }
    for char in text:
        if "a" <= char <= "z" or "0" <= char <= "9":
            yield char
        elif "A" <= char <= "Z":
            yield "shift-" + char.lower()
        elif char in aliases:
            yield aliases[char]
        else:
            raise ValueError("Unsupported QEMU key: %r" % char)


def main():
    parser = argparse.ArgumentParser()
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--baseline", action="store_true")
    target.add_argument("--run-id", help="CI run ID of experimental Haiku VM")
    target.add_argument("--local-id", help="8-character local build source SHA, optionally -trial1..9")
    parser.add_argument("command", choices=("info", "screenshot", "type",
                                            "terminal"))
    parser.add_argument("text", nargs="*")
    args = parser.parse_args()
    base = Path.home() / "Developer" / "Haiku"
    if args.baseline:
        monitor = base / "vm/haiku-ai-baseline-monitor.sock"
        out = base / "vm/haiku-ai-baseline-latest.ppm"
    else:
        if args.local_id is not None:
            if re.fullmatch(r"[0-9a-f]{8}(?:-trial[1-9])?", args.local_id) is None:
                parser.error("local ID must be eight lowercase hex digits, optionally -trial1..9")
            folder = base / "ai-images" / ("run-local-" + args.local_id)
        else:
            if not args.run_id.isdecimal():
                parser.error("run ID must contain only decimal digits")
            folder = base / "ai-images" / ("run-" + args.run_id)
        monitors = [folder / "haiku-ai-minimum-monitor.sock",
                    folder / "haiku-ai-regular-monitor.sock"]
        available = [path for path in monitors if path.is_socket()]
        if len(available) != 1:
            parser.error("exactly one active image monitor is required")
        monitor = available[0]
        out = folder / "haiku-ai-current-screen.ppm"
    if args.command == "type" and not args.text:
        parser.error("type requires guest shell text")
    keys = list(keyboard(" ".join(args.text))) if args.command == "type" else []
    if not monitor.is_socket():
        parser.error("QEMU monitor missing: " + str(monitor))
    with socket.socket(socket.AF_UNIX) as sock:
        sock.settimeout(8)
        sock.connect(str(monitor))
        receive_prompt(sock)
        if args.command == "info":
            print(exchange(sock, "info status"))
            print(exchange(sock, "info block")[-1000:])
        elif args.command == "screenshot":
            exchange(sock, "screendump " + str(out))
            if not out.exists() or out.stat().st_size == 0:
                raise RuntimeError("No screenshot created")
            print("SCREENSHOT=" + str(out))
        elif args.command == "terminal":
            # Haiku's known Ctrl/Meta-Alt-T shortcut worked on the
            # CI-built minimal GUI; do not assume the shell has focus
            # until its new window has visibly appeared.
            exchange(sock, "sendkey meta_l-alt-t")
            print("Requested Haiku Terminal via guest keyboard shortcut")
        else:
            for key in keys:
                exchange(sock, "sendkey " + key)
                time.sleep(.1)
            exchange(sock, "sendkey ret")
            print("Guest received %d keyboard events" % (len(keys) + 1))


if __name__ == "__main__":
    main()
