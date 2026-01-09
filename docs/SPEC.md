Policy Engine — Frozen Specification (v1.3.2)

Status

Execution-sealed
This document defines the complete and immutable contract for the Policy Engine implemented in STEP 4.

Any deviation from this specification must refuse system boot.

⸻

Purpose

The Policy Engine exists to determine whether the system is allowed to exist.

It is not configuration loading.
It is constitutional validation.

If the policy violates this spec, the system must fail fast and refuse to boot.

⸻

Scope

This specification governs:
	•	Policy file structure
	•	Validation rules
	•	Failure behavior
	•	Public API contract
	•	Determinism and immutability guarantees

This spec does not define:
	•	Memory runtime behavior
	•	AI reasoning logic
	•	Execution pipelines

⸻

Policy File

Required File

policy_v1.3.2.yaml

This file is the single source of truth.

⸻

Required Top-Level Keys

All of the following keys must exist at the top level:
	•	version
	•	status
	•	contract
	•	driftforbidden
	•	non_negotiable_rules
	•	claim_confidence
	•	memory
	•	uncertainty
	•	groundingprotocol
	•	pacing
	•	llmexecutor
	•	outputvalidation
	•	error_messages
	•	bootvalidation

Missing any key → FAIL BOOT

⸻

Fixed Value Enforcement

The following values must match exactly:

Key	Required Value
version	"1.3.2"
status	"execution-sealed"
contract	"binding"
driftforbidden	true

Any mismatch → FAIL BOOT

⸻

Context Completeness Rule

For every context defined in:

memory.requiredparametersbycontext

The same context must exist in:

groundingprotocol.questions

And vice-versa.

Missing or extra context → FAIL BOOT

⸻

Grounding Protocol Rules
	•	groundingprotocol.numquestions must be exactly 5
	•	Every context must have exactly 5 grounding questions
	•	sixthquestionrule must exist
	•	sixthquestionrule must contain:
	•	decision_logic
	•	examples

Violation → FAIL BOOT

⸻

Memory Rules

The following rules are strict:
	•	memory.decay.days == 180
	•	memory.decay.reconfirmation_message must exist
	•	memory.promotion must contain:
	•	gate1
	•	gate2
	•	gate3
	•	memory.conflict_resolution must exist

Violation → FAIL BOOT

⸻

Non-Negotiable Rules
	•	non_negotiable_rules must be a list
	•	The list must contain at least 5 entries

Violation → FAIL BOOT

⸻

Uncertainty Matrix Rules
	•	uncertainty.binarychecks must contain exactly 3 items
	•	uncertainty.mapping must define:
	•	allyes
	•	oneno
	•	twoormoreno

Violation → FAIL BOOT

⸻

Pacing Rules

For each mode in pacing.modes:

Required keys:
	•	targettokens
	•	hardcap
	•	multiturn

Constraints:
	•	hardcap ≤ 5000
	•	targettokens ≤ hardcap

Violation → FAIL BOOT

⸻

Error Code Completeness Rule (STRICT)

Every error code referenced in:
	•	outputvalidation.mustcheck
	•	Validator test specification (hardcoded list)

Must exist in:

error_messages

Missing code → FAIL BOOT

⸻

Failure Behavior

On any validation failure:
	•	Raise PolicyValidationError
	•	Include:
	•	section
	•	expected
	•	found
	•	context
	•	System must refuse to boot

No fallback. No recovery.

⸻

Determinism & Immutability Guarantees

The Policy Engine guarantees:
	•	No mutation of policy data
	•	No randomness
	•	No timestamps
	•	No side effects
	•	Identical input → identical output

Multiple loads of the same valid policy must produce identical API results.

⸻

API Contract (High-Level)

The Policy Engine exposes read-only APIs only.
	•	All returned values are deep copies
	•	Invalid keys raise KeyError
	•	No setters exist

(Full API contract defined in API.md)

⸻

Bootstrap Order (Immutable)

The engine boot sequence is fixed:
	1.	Load YAML from disk
	2.	Parse into Python dict
	3.	Validate against this spec
	4.	If valid → system ready
	5.	If invalid → system refuses to exist

⸻

Change Policy

This spec is frozen.

Any change requires:
	•	New version number
	•	Explicit approval
	•	Updated tests
	•	Re-lock of STEP 4

⸻

Status Summary
	•	Specification: Final
	•	Version: 1.3.2
	•	Drift: Forbidden
	•	Enforcement: Strict