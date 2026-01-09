Policy Engine

Overview

The Policy Engine is a deterministic boot-time system responsible for loading, validating, and exposing a single authoritative policy file (policy_v1.3.2.yaml).

This is not configuration loading.
This is constitutional bootstrapping.

If the policy is invalid, the system refuses to exist.

⸻

Design Principles
	•	Deterministic – Same input policy always produces the same behavior
	•	Immutable – Policy data cannot be modified after boot
	•	Idempotent – Multiple loads yield identical results
	•	Fail-fast – Any violation prevents boot
	•	Single source of truth – All rules come from policy, not code
	•	Explainable failures – All failures include exact reason and context

⸻

Project Structure

policy_engine/
  ├── __init__.py
  ├── __main__.py        # CLI entry point
  ├── loader.py          # YAML loading only
  ├── validator.py       # All validation logic
  ├── api.py             # Read-only accessors
  ├── errors.py          # Canonical error type
  └── policy_engine.py   # Bootstrap orchestration

tests/
  ├── test_loader.py
  ├── test_validator.py
  ├── test_api.py
  └── test_policy_engine.py


⸻

Installation

Requirements
	•	Python 3.10+
	•	PyYAML
	•	pytest

Setup

python -m venv .venv
source .venv/bin/activate
pip install pyyaml pytest


⸻

Usage

CLI Validation

Validate a policy file from the command line:

python -m policy_engine ./policy_v1.3.2.yaml

Exit Codes

Code	Meaning
0	Policy is valid
1	Validation failed
2	Policy file not found
3	YAML parse error / invalid structure


⸻

Programmatic Usage

Boot the Policy Engine

from policy_engine.policy_engine import PolicyEngine

engine = PolicyEngine("policy_v1.3.2.yaml")

If the policy is invalid, initialization raises an exception and the system does not start.

⸻

Access Policy Data (Read-Only)

from policy_engine.api import PolicyAPI

api = PolicyAPI(engine.policy)

limits = api.get_token_limits("normal")
questions = api.get_grounding_questions("learning")

All API calls return deep copies.
Mutating returned data does not affect internal state.

⸻

Error Handling

All validation failures raise a PolicyValidationError with a strict format:

Policy validation failed at [section]:
  Expected: [expected condition]
  Found: [actual value]
  Context: [location]

This format is stable and relied upon by:
	•	CLI
	•	Tests
	•	CI pipelines

⸻

Testing

Run the full test suite:

pytest

Test coverage includes:
	•	Loader failures
	•	Validation rule enforcement
	•	API immutability
	•	Engine bootstrap behavior
	•	Idempotency guarantees

⸻

What This Engine Does NOT Do
	•	It does not execute AI logic
	•	It does not mutate memory
	•	It does not infer rules
	•	It does not tolerate partial correctness

This engine only decides whether the system is allowed to exist.

⸻

Status
	•	STEP 4 — Policy Engine: Complete and locked
	•	All rules enforced
	•	All APIs immutable
	•	All tests passing

⸻

License / Usage

Internal project component.
Not intended for public distribution.