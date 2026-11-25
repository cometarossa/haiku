# Negative baseline private reply probe
Native compilation on Beta6 hrev59866 succeeded without warnings in
both attempts. First attempt exited 3; detailed retry isolated failure
to Read<ssize_t>(&offset), B_BAD_VALUE. No valid reply evidence.
Beta6 is an older revision than the experimental image. A wire format
difference is plausible, but not established: the local source checkout
is shallow and does not contain the exact Beta6 server revision.
Do not infer received allocation flags or bypass the failed check.
Use the known V13 source/image pairing for the next native probe.
Failed attempts are retained; diagnostic binary remains separately
hashed on the Mac. The phase campaign was running on a separate VM
during these brief native compilations; host load is not isolated.
