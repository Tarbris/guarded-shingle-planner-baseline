# Guarded Catalog baseline

This is a newly authored, AI-assisted baseline for an original repository-change
proposal. It is not a pre-existing third-party upstream or an implementation of
the benchmark task. The MIT-licensed code uses only the Python standard library.

Run offline on Linux with Python 3.9 or newer:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
python3 -m guarded_catalog
```

The CLI reads one JSON object per line and emits one response per line. Example:

```json
{"op":"put","id":"draft","text":"A public document.","priority":5,"protected":false}
{"op":"put","id":"reviewed","text":"a PUBLIC document","priority":0,"protected":true}
{"op":"exact_plan"}
```

The API exports `ExactCatalog` and `tokenize`. `put(id,text,priority=0,
protected=False)` atomically replaces a document. `delete(id)` returns whether it
existed; `snapshot()` returns fresh dictionaries in ASCII ID order.
IDs match `[A-Za-z0-9_-]{1,64}`. Priorities are signed 32-bit integers, excluding
booleans. `protected` must be a boolean. Text must be a valid Unicode string.
Invalid calls raise `ValueError` without altering state.

Tokenization uses ASCII `[A-Za-z0-9]+` runs and lowercases them. Punctuation and
non-ASCII characters separate tokens. `exact_plan()` groups identical complete
token sequences; empty-token documents remain separate. It chooses the smallest
`(priority,id)` as representative and returns `groups` ordered by representative,
each containing `representative` and ASCII-sorted `members`. This old API treats
`protected` only as stored metadata. Returned values cannot mutate catalog state.

The CLI supports exact-field commands: `put` requires `op,id,text,priority,
protected`; `delete` requires `op,id`; `snapshot` and `exact_plan` require only
`op`. Success is `{"ok":true,"result":...}`; rejection is
`{"ok":false,"error":"invalid-command","detail":...}`. Error detail wording is
not a stable API. The program continues after a rejected line.

The proposed near-duplicate planner is deliberately absent. The baseline has no
shingle index, approximate or exact near-duplicate join, protected merge forest,
or complete answer to the proposed extension. The target is offline,
single-process and single-threaded; the baseline makes no Spark, distributed
execution, durability or concurrent-access claims.
