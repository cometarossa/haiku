# Independent local image build
AI-assisted independent research fork. GitHub returned HTTP 422
"Actions has been disabled for this repository" twice on 25 November
despite permissions enabled=true and workflow active. Repository
public, not archived/disabled, authenticated user has admin. GitHub
status reported Actions operational. 93 historical runs: 78 automatic
evidence validations, 10 regular images, 3 minimum images, 2 toolchain.
Exact cause unconfirmed; ask GitHub Support to review repository/account
restriction. Do not bypass enforcement by creating alternate GitHub
accounts or repeatedly toggling settings.

ZimaBlade preflight 25 Nov: /DATA/Documents/haiku-ai-lab, x86_64,
83 GiB available, existing Ubuntu24 builder tag and partial toolchain,
4 logical CPUs, 15 GiB total RAM, 8.6 GiB available, swap in use.
Fast-forwarded clean clone to V10 f7e36bf2; bounded offline Jam
preflight passed. No full compiler or image yet. Prefer dedicated
Ubuntu VM on iMac/EPYC server for routine heavy workloads; do not
overload Zima production services.

New build-regular-local.sh uses the working regular CI configure/Jam
commands, preserves exact source and tools revisions, locks build
directory, retains partial logs, publishes compressed artifact and
both checksums only after success. Keep source and buildtools on a
Linux filesystem in a dedicated workspace; do not mount production
disks or GitHub credentials in build container. Configure once and
reuse local objects where possible. Dockerfile adds missing image tools.
Build a new image tag (do not overwrite existing):
    docker build -t haiku-ai-builder:ubuntu24-v2 -f haiku-ai/experiments/ai-lab/Dockerfile.builder haiku-ai/experiments/ai-lab
Then from dedicated workspace containing haiku-ai and buildtools:
    docker run --rm --init --cpus=2 --memory=4g --memory-swap=4g \
      --pids-limit=512 --cap-drop=ALL --security-opt=no-new-privileges \
      --user "$(id -u):$(id -g)" -e HOME=/tmp \
      -v "$(pwd):/work" -w /work \
      haiku-ai-builder:ubuntu24-v2 \
      timeout --signal=TERM --kill-after=30s 7200 \
      sh /work/haiku-ai/experiments/ai-lab/build-regular-local.sh
Network is required for fetching image packages, unlike earlier offline
preflight. No persistent background service. Copy successful artifact
to independent Sequoia build directory; verify both hashes, then boot
in isolated QEMU overlay. Full local image path not yet executed.

## Local artifact import (Mac)
After the build has completed successfully, transfer the provenance and
three artifact files to a dedicated Mac staging directory. Then:
    HAIKU_LOCAL_IMPORT_ONLY=1 sh experiments/ai-lab/boot-regular-macos.sh --local /path/to/artifact
    HAIKU_REGULAR_VNC_DISPLAY=14 sh experiments/ai-lab/boot-regular-macos.sh --local /path/to/artifact
    python3 experiments/ai-lab/guest-hmp.py --local-id <8-hex-source-id> info
Use a free VNC port only. The importer checks source ancestry, revision,
compressed and raw hashes, rejects conflicting cached provenance, and
uses a separate run-local-* target. Five isolated synthetic import
checks passed on Mac (wrong compressed hash, wrong raw hash, correct
import, cache reuse, conflicting cache). No real local image boot tested.
The ZimaBlade build uses the previous source snapshot 12b5c9ec,
not this documentation/host-helper commit. Do not update the running
builder's checkout while it is compiling.
