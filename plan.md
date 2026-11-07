# Dependency security audit plan

Previous plan preserved in `plan20261102.md`; consult it for project context and unfinished work.

- [x] Review project instructions, working tree, dependency manifests, environments, and prior audit results.
- [x] Audit the requirements using the intended Python environment. The previous isolated resolution timed out; investigate the resolution and avoid leaving child processes running.
- [x] If this project uses Node.js, inventory its runtime declarations and environments. Require Node 22 or newer; update Node 22 to at least 22.23.4, Node 24 to at least 24.22.1, and Node 26 to at least 26.12.1. Verify compatibility and the project’s build and tests after updates.
- [x] Apply only compatible fixes that preserve functionality; record advisory IDs, versions, dependency paths, and any findings that cannot be safely fixed.
- [x] Repeat the applicable audits and run the project’s tests or build; document failures and any limits on verification.
- [x] Review the diff and existing staged changes. If changes are verified to preserve functionality, commit the dependency changes together with unstaged `plan*.md` files, then push to the configured remote; otherwise report the blocker without pushing.

Follow-up: `uv pip compile --python-version 3.12 requirements.txt` resolved the full dependency graph; pip-audit found no known vulnerabilities in both the original pins and the resulting graph. GitHub reports no open Dependabot alerts. The earlier pip-based timeout was not reproduced with uv; its precise cause remains unknown. No Node.js manifest was found. Prior isolated test and environment limitations are recorded in the previous plan.

Verification: isolated Python 3.12 tests with Streamlit 1.66.1 and OpenAI 1.41.0 ran against copied code and in-memory SQLite: 9 passed, with the same two pre-existing failures documented in the previous plan (outdated insert signature and thread-title expectation). No dependency versions changed; this targeted environment did not install the full GPU stack. The previous pip resolver timeout remains unexplained, but the full pinned graph resolved with uv and audited cleanly.
