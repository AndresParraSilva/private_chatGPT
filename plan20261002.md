# Dependency vulnerability remediation plan

Dependabot's saved alert page identifies vulnerable pins in `requirements.txt` for PyJWT, urllib3, Tornado, virtualenv, and GitPython. The listed releases below address the corresponding alerts; virtualenv 21.7.13 covers its prompt/configuration and activation-script issues as well as the seed-wheel integrity alert.

## To-Do

- [x] Update only these pins in `requirements.txt`: `PyJWT==2.15.0`, `urllib3==2.8.0`, `tornado==6.5.9`, `virtualenv==21.7.13`, and `GitPython==3.1.62`. The PyJWT and virtualenv targets were advanced after the first targeted audit found newer advisories fixed in 2.15.0 and 21.7.13.
- [x] Audit the updated vulnerable packages against the current vulnerability database; the five upgraded packages have no known vulnerabilities.
- [x] Checked for a project virtual environment; none is present, so installed-package reconciliation was unavailable. No unrelated packages were added.
- [x] Ran both existing unittest modules with temporary runtime dependencies. Two tests fail for existing application/test mismatches: title increment expected `Example (3)` but returned `Example`, and `test_db_insert_message` calls a function with an outdated signature.
- [x] Recorded task outcomes in this plan.
