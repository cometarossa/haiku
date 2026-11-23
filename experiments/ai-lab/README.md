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
