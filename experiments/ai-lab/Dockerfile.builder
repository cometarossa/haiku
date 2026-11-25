# AI-assisted experimental fork; never submit to official Haiku upstream.
# Native x86_64 Linux toolchain for cross-building Haiku x86_64.
FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential ca-certificates git curl wget python3 gawk \
    bison flex nasm libgmp-dev libmpfr-dev libmpc-dev \
    zlib1g-dev libzstd-dev texinfo autoconf automake libtool \
    libncurses-dev pkg-config xz-utils unzip cmake libexpat1-dev xorriso mtools zstd util-linux \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /work
CMD ["/bin/bash"]
