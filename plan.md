# Private ChatGPT dependency vulnerabilities

- [x] Re-audit pinned requirements and the actual runtime, recording `msgpack`, `pyasn1`, and `tornado` versions and advisory paths.
- [x] Establish an isolated representative environment and tests with disposable databases and mocked external APIs; preserve private chat data and do not send messages.
- [x] Evaluate compatible fixes, initially `msgpack` 1.2.3 or later, `pyasn1` 0.6.5 or later, and `tornado` 6.6 or later, preserving unrelated pins.
- [x] Re-audit and run safe offline checks against the baseline; document any compatibility or verification blockers.
- [x] Commit and push only verified dependency changes.

Verification notes: PyPI's advisory API reports no known advisories for the 161 current pins. No running app or identifiable project runtime was found. A disposable Python 3.12 environment excluded Torch, Triton, and NVIDIA packages. Before and after upgrades, 9 of 11 tests passed; `test_db_insert_message` uses an outdated signature and `test_get_new_thread_title_with_extension` has an existing expectation mismatch. The environment's dependency check also reported the same existing typing-inspection mismatch and missing pytokens and python-discovery dependencies before and after the upgrade. Targeted package smoke checks and Python compilation passed. The pip-audit launcher was broken and an isolated pip-audit invocation stalled; PyPI's advisory API was queried for each pin instead.

GitHub additionally reported GHSA-cx6f-vjhg-g3cc for virtualenv 21.14.10, absent from the PyPI advisory feed. Updated it to 21.14.13 and successfully created a disposable environment with it. Installing it also installed its python-discovery dependency, resolving that baseline check issue. GitHub still displayed the alert immediately after the push; its status may take time to update.
