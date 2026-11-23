# x86_64 cross-compiler bootstrap — 23 November 2026

**AI-assisted fork status; the native Haiku x86_64 OS has NOT been
built from this fork yet.**

## Verified

- Ubuntu 24.04 container on ZimaBlade, GCC 13, Python 3.12,
  GNU awk, NASM; Haiku host-only configure passed.
- Haiku source starting at fork revision 94e6bfa4, upstream base a479fc07.
- Independent buildtools source revision 33d46bf5.
- The cross-tools source build ran with 2 CPU and 4 GiB RAM,
  network disconnected, 256 process limit, no added capabilities.
- GNU binutils for target x86_64-unknown-haiku were built and installed:
  target x86_64-unknown-haiku-as and x86_64-unknown-haiku-ld exist.
- The GCC stage began and progressed through build dependencies
  including GMP/ISL, but x86_64-unknown-haiku-gcc **was not produced**.

## Boundaries and next action

- An initial outer-shell timeout interrupted only the Docker client;
  the container kept compiling. It was explicitly stopped afterwards.
  The production machine retained its original 19 application containers.
- Build outputs remain under /DATA/Documents/haiku-ai-lab/haiku-ai/generated.
  They are partial and may be reused by a subsequent invocation.
- Use experiments/ai-lab/run-limited-builder.sh with --configure:
  the inner-container timeout bounds the entire build safely and
  prevents an orphaned container.
- Run the complete cross-toolchain build to successful exit, then
  produce an isolated Haiku QEMU boot image. Only then try a fork patch.
- Do **not** submit code, reports or AI-assisted materials upstream.
