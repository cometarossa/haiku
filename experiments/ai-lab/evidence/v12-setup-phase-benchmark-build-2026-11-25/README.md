# V12 setup-phase native probe
Source 60c93c19, separately compiled on the Beta6 guest with
-DLAB_SETUP_PHASES, -O2, using the recorded compiler. Source and
binary hashes verified. Signedness and missing-field-initializer
warnings recorded: omitted aggregate members are zero initialized
and all phase fields are assigned before validation on success.
No errors in compilation. Instrumented binary is not interchangeable
with corrected uninstrumented timing evidence.
