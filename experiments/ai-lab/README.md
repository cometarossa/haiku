# Haiku experimental lab — AI-assisted fork

**Provenance:** The contents of this directory and the fork-specific
`AGENTS.md` were prepared with AI assistance (November 2026).
This independent research fork is **not affiliated with Haiku's
maintainers**, and no AI-assisted contributions will be submitted
to the official Haiku project.

Upstream source: https://github.com/haiku/haiku
Research fork: https://github.com/cometarossa/haiku
Working branch: `ai-experimental`

## Mission

Build a reproducible x86_64 Haiku development loop for correctness
testing in QEMU. Our first subsystem target is native Media Kit /
media_server stability (node lifetime, repeated open/close, error
handling), followed by app_server and kernel synchronization as
supported by isolated regression tests.

## Safety and environment

- The host Mac has a case-insensitive default APFS volume; Haiku's
  source tree has colliding case-sensitive paths. **Do not build there.**
- The sources and buildtools reside on a 20 GiB case-sensitive APFS
  sparsebundle mounted at `/Volumes/HAIKU_DEV_CS`. The persistent image
  lives at `~/Developer/Haiku/HAIKU_DEV_CS.sparsebundle`.
- A symlink `~/Developer/Haiku/haiku-ai` points to the source checkout.
  Mount the sparsebundle before accessing it after reboot.
- Keep the official beta6 VM disk intact. Create separate disposable
  build images and test disks. Do not modify any production disks.
- The host has limited free physical disk space, so check it before
  building a full image. The image's virtual size is not preallocated.
- The Jam host build succeeded. On the Mac, a Clang cross-build configure
  currently reaches a missing `libsupc++.a` dependency, so a full
  toolchain build and QEMU boot from new sources are **not yet verified**.
  This document must not be treated as proof of a full build.

## Development gates

1. **Baseline:** Verify source revision, buildtools revision,
   case sensitivity, available space, and native build dependencies.
2. **Build:** Cross-compile Haiku x86_64 and record logs and artifacts,
   without writing to the persistent beta6 qcow2.
3. **Test:** Boot only a disposable build image in a new QEMU VM,
   run smoke tests and capture serial/GUI evidence.
4. **Regressions:** Write minimal deterministic Media Kit tests,
   validate failures on the baseline, then compare proposed changes.
5. **Publication:** Keep evidence and AI-assisted experimental changes
   in this fork only. Never submit these materials upstream.

Run `sh experiments/ai-lab/doctor.sh` for a read-only workspace check.

## Isolated Linux build option

The Dockerfile.builder defines a Linux host for Haiku cross-builds.
Mount source and buildtools as /work/haiku-ai and /work/buildtools.
The read-only preflight mode is build-in-linux.sh --check.
The explicit --configure mode begins the GCC toolchain bootstrap and
must only be run with CPU/memory limits and plenty of free disk space.
See ROADMAP.md for status. Neither mode touches persistent beta6 disks.

## Verified Linux builder smoke test (2026-11-23)

ZimaBlade hosts an isolated Ubuntu 24.04 container image
haiku-ai-builder:ubuntu24. With no network, two CPU cores maximum,
3 GiB memory limit, no added Linux capabilities and no new privileges,
the host compiled Jam and executed its version check successfully.
Haiku host-only configure also passed in the isolated builder. It
reported missing setfattr (Linux extended-attribute helper). These tests
validate prerequisites only: cross-GCC, a bootable OS image, and Media
Kit regression tests have not yet been built.

## Cross-toolchain build on ZimaBlade

On ZimaBlade the laboratory checkout lives in
/DATA/Documents/haiku-ai-lab; build artifacts are stored there.
The container image is haiku-ai-builder:ubuntu24.

Use run-limited-builder.sh --check for a bounded dependency test,
or --configure for a 10-minute incremental toolchain build segment.
Timeout runs INSIDE the container, not around the Docker client,
so no orphan build container is left behind. The Zima-local incremental toolchain is not yet complete; an
independent GitHub Actions toolchain build has succeeded.
See TOOLCHAIN-STATUS-2026-11-23.md.

## Boot the first CI-built Haiku image on macOS

Once a Haiku x86-64 minimum image CI run has completed successfully,
use the guarded script boot-minimum-macos.sh with the run ID. The script
downloads the compressed image through the GitHub CLI, verifies both
SHA-256 manifests, decompresses the raw image, creates a copy-on-write
QCOW2 backing overlay, and launches a new QEMU/HVF VM on localhost VNC
port 5912 using the existing private Haiku VNC password. Original beta6
virtual disks are never modified.

The script is guarded against unfinished CI runs, corrupted artifacts,
missing host tools and VNC port conflicts. It must not be invoked
with unknown or untrusted CI run IDs. Actual image boot is unverified
until the minimum image workflow succeeds.

After booting an experimental CI image, run the guarded
probe-minimum-macos.sh with the run ID to capture its actual QEMU screen,
inspect info status, and read the guest serial log without writing
inside the guest. Only a visible Haiku desktop or a verified boot
console provides evidence that the OS successfully booted.


## Full desktop image with patched MediaPlayer

The \`haiku-build-regular.yml\` workflow is a **manual-only** alternative
to the minimum boot image. It builds Haiku \`@nightly-raw\`, whose regular
desktop content includes MediaPlayer from this fork, compresses the
disk and uploads only the artifact and short-term logs. The first regular desktop build is run 45285916285; as of
2026-11-24 the cross-toolchain step is in progress.

The full desktop image is still an independent AI-assisted fork and
is never submitted upstream. Do not treat a successful compile as
proof the GUI works without a separate QEMU boot and smoke test.


### Full desktop image QEMU test harness

After the regular desktop workflow completes successfully, use
\`boot-regular-macos.sh <regular-run-id>\` to independently verify SHA256
checksums and launch the full Haiku desktop under QEMU/HVF with a
throwaway overlay and localhost VNC on port 5913. The baseline beta6
(port 5911) and experimental minimum image (port 5912) are not modified.

Use \`probe-regular-macos.sh <regular-run-id>\` to collect QEMU monitor
status, screenshot and any serial logs. Validate that the regular
desktop actually includes our fork-patched MediaPlayer and run the
cover-art tests before calling MediaPlayer GUI integration complete.

### Host-side QEMU terminal/screenshot test helper

The independent-fork guest-hmp.py script operates only on known
local Haiku lab VM UNIX monitor sockets. Use --baseline or --run-id to
choose a target, followed by info, screenshot, or type. The type
action requires explicit text and injects guest keyboard events.
Example: python3 guest-hmp.py --run-id 123456789 screenshot.
A GUI Terminal must have input focus before entering shell commands.
The helper cannot reboot or write virtual disks directly.


## First verified CI-built Haiku boot (2026-11-24)

GitHub Actions run 45282976284 successfully produced a 300 MiB
minimum raw disk image. Both SHA256 checks passed on macOS.
QEMU/HVF booted it and reached the visible Haiku desktop. The
original beta6 disk remains unchanged. See
evidence/fork-minimum-boot-2026-11-24/ for source revision,
screenshot, artifact checksums, and limitations.

This is a minimal OS smoke test, not a complete MediaPlayer runtime.
