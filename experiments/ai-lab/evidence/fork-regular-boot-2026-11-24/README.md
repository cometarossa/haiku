# First regular desktop boot and MediaPlayer failure — 2026-11-24

AI-assisted independent research fork. GitHub Actions run 45285916285
built revision d1e0b80c, 650 MiB raw image. Both image hashes verified.
QEMU/HVF reached welcome screen and desktop after Try it out, with
4 vCPUs, 8 GiB RAM, separate QCOW2 overlay; beta6 disk untouched.
Guest uname shows hrev60465+ai_d1e0b80c. Three GUI fixture hashes passed.
MediaPlayer present and launched, but opening cover_h264.mp4 crashed:
Divide error in Controller::_TimePosition(), during PlaybackManager::Init.
The GUI single-frame test is FAILED. Other media tests remain pending.
The likely cause is truncation of a positive duration to zero frames.
A minimum-one-frame patch and host arithmetic regression test are
provided separately; this does not establish a corrected guest boot.
