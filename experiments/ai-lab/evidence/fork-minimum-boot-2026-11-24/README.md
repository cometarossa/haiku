# First successful fork-built Haiku x86_64 boot on macOS QEMU/HVF

Research fork: cometarossa/haiku, branch ai-experimental.
Original Haiku upstream base: hrev60465. AI-assisted fork artifact.
This is not an official Haiku build or an upstream contribution.

## Source and artifact provenance

GitHub Actions CI:
https://github.com/cometarossa/haiku/actions/runs/45282976284

Exact CI checkout commit:
2a23e157e0eddd636d32d440c8c01dc7291e71e3

- Ubuntu CI cross-toolchain successfully built GCC and binutils for Haiku
  x86_64, compiled the minimum raw disk image, compressed it, and
  uploaded sha256 checksum manifests.
- Mac downloaded the GitHub artifact, verified both the zstd and raw
  SHA256 values, and generated a separate copy-on-write QCOW2 backing
  overlay. The reference beta6 guest disk was not modified.
- Uncompressed raw image: 300 MiB (314,572,800 bytes).
- QEMU 10.0.2 HVF, pc machine, Penryn virtual CPU, 4 vCPUs, 4 GiB RAM,
  standard VGA, RTL8139 virtual network, legacy IDE disk.
- Host-local VNC port 5912 with password enabled; UNIX QEMU HMP socket.
- QEMU HMP reported VM status running, with the overlay as drive.
- The screenshot haiku-fork-minimum-desktop.png was captured directly
  from the QEMU monitor via screendump and inspected visually.
  It shows the actual Haiku desktop, Tracker, Deskbar, Home and Trash.

## Known limitations, do not overclaim

- This is the MINIMUM profile, not the complete Haiku desktop image.
  A blue desktop and live app_server prove bootability and UI presence,
  but do not prove full multimedia or browser compatibility.
- The serial console reports some missing optional components, including
  libharfbuzz.so.0, libmedia.so, libgame.so and libscreensaver.so.
  See boot-serial-warnings-excerpt.txt. These omissions make the minimum
  image insufficient to validate our patched MediaPlayer executable.
- A separate manual CI build for the full @nightly-raw desktop image,
  including MediaPlayer, must pass and boot before we can test the actual
  integrated GUI fix.
- No native hardware performance measurements or bare-metal claims.

The full local 42 KiB serial log and original disk image are retained
with the Mac's isolated VM; only the selected warnings and image/
screenshot checksum manifests are published here.

## Native guest identity and interactive shell

Once the fork-built GUI booted, the QEMU keyboard shortcut opened the
Haiku Terminal. The uname -a command was executed **inside the guest**.
Its visible output contains:

    Haiku shredder R1~beta6+development hrev60465+ai_2a23e157

This revision matches the CI checkout SHA prefix in the build log
and confirms the VM is not the separately installed official beta6.

The native open /boot/home command launched Tracker's home folder,
confirming functioning GUI application launch and windowing. In a
second focused Terminal, sysinfo completed and reported the guest
CPU's virtualized feature set, userland resources, and ~4 GiB of RAM.
Both terminal results are preserved as unmodified QEMU screen captures:
haiku-fork-minimum-uname.png and haiku-fork-minimum-sysinfo.png.

These smoke tests still do not exercise MediaPlayer or video playback.
