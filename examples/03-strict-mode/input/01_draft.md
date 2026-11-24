The decoder fills every field of the record in parallel, so latency no
longer scales with the number of fields the schema requires. We measured
median latency across three seeds and two input lengths, holding model size
and data fixed.

Under matched quality the parallel arm is faster, and the gap is stable
enough to matter for deployments that stream records continuously through
long shifts without pausing to batch, which is the regime where sequential
decoding pays its price. The parallel arm needs a
fixed canvas, and the schema must be known before decoding starts.
