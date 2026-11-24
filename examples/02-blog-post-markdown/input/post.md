# Shipping a log parser without drama

Log parsing looks boring until it breaks production. A pipeline that turns
raw cluster logs into structured records has to keep pace with ingestion,
or the monitoring stack falls behind and nobody notices until the postmortem.

We replaced a sequential decoder with a parallel one and measured what
changed. Median latency per event dropped from 47 ms to 23 ms under the
same hardware budget. Quality stayed flat: every required field is filled
on the same held-out split, on three seeds, at two input lengths.

The interesting part is not the speed. It is that the latency no longer
scales with the number of fields in the record. The old decoder paid for
each field in tokens; the new one pays per record. That changes which
deployments are viable.
