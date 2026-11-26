# V20 eight-stream aborted preflight
No playback trial launched. Previous four-stream campaign left its
proxy marker because shell ownership flag x was overwritten by
window position x. AND-list tests failed to reject the residual
marker under set -e. Four-stream native metrics remain valid
but cleanup was incomplete, contrary to its original gate report.
Host runner stopped after guest returned to prompt; no VM stopped.
Fix 8f10ccdd uses independent ownership flags and explicit checks.
Regression test exercises actual shell marker cleanup and refusal.
Cleanup first attempt stopped at unsupported argumentless mount;
second verified marker empty, other markers absent, RAMFS only
input files, then removed known lab marker and unmounted RAMFS.
Retried separately; no fabricated benchmark outcomes.
