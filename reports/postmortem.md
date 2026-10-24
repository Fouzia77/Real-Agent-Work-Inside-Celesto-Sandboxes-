# Failure post-mortem

**Evidence status:** the checked-in reliability rows are structural fixtures used to exercise the report validator. They are not claimed to be measured Celesto Cloud runs. Replace them by running `python scripts/run_eval.py 20` with a real Celesto API key before submitting the final evidence.

The fixture includes two failures among twenty rows to ensure the summary preserves failed attempts instead of deleting them. In a live evaluation, investigate each failure by separating guest boot errors, command-gate denials, command exit codes, proof-file verification failures, provider rate limits, and cleanup errors. Keep each failed row and its original sandbox name. The most important improvement is to capture the SDK's concrete error and step number rather than retrying blindly.

The current agent is intentionally deterministic and has a small command surface, so it tests sandbox dispatch and proof verification rather than LLM reasoning quality. A production version should add bounded retries only for known transient errors, persist a checkpoint before risky actions, and mark uncertain outcomes separately from confirmed failures. Do not report a success until the proof file has been read back and verified. Track boot-to-ready separately from total wall time, and derive all summary statistics from raw rows using the evaluator's stated percentile convention.
