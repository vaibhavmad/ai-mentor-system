Policy Engine — API Contract

Overview

This document defines the public, read-only API exposed by the Policy Engine.

These APIs provide safe access to policy data after successful boot validation.

Rules
	•	All APIs are read-only
	•	All return values are deep copies
	•	No internal references are ever returned
	•	Invalid keys raise KeyError
	•	No setters exist

⸻

Initialization

The API operates on an already-validated policy.

from policy_engine.policy_engine import PolicyEngine
from policy_engine.api import PolicyAPI

engine = PolicyEngine("policy_v1.3.2.yaml")
api = PolicyAPI(engine.policy)

If validation fails, PolicyEngine refuses to initialize and no API access is possible.

⸻

API Methods

1) get_token_limits(mode: str) -> dict

Description
Returns token limits for a given pacing mode.

Parameters
	•	mode — pacing mode name (e.g., "normal", "careful", "deliberative")

Returns

{
  "targettokens": int,
  "hardcap": int,
  "multiturn": bool
}

Errors
	•	KeyError if the mode does not exist

Example

limits = api.get_token_limits("normal")


⸻

2) get_uncertainty_matrix() -> dict

Description
Returns the uncertainty configuration, including binary checks and mappings.

Returns

{
  "binarychecks": list,
  "mapping": {
    "allyes": str,
    "oneno": str,
    "twoormoreno": str
  }
}

Example

uncertainty = api.get_uncertainty_matrix()


⸻

3) get_user_choice_template() -> dict

Description
Returns the user choice template and constraints.

Returns

{
  "options": dict,
  "forbidden": list
}

Errors
	•	KeyError if the section is missing

Example

choices = api.get_user_choice_template()


⸻

4) get_grounding_questions(context: str) -> list[str]

Description
Returns grounding questions for a specific context.

Parameters
	•	context — one of the defined contexts (e.g., "learning", "planning")

Returns

[
  "Question 1",
  "Question 2",
  "Question 3",
  "Question 4",
  "Question 5"
]

Errors
	•	KeyError if the context does not exist

Example

questions = api.get_grounding_questions("learning")


⸻

5) get_output_validation_rules() -> dict

Description
Returns output validation rules.

Returns

{
  "mustcheck": list
}

Example

rules = api.get_output_validation_rules()


⸻

6) get_claim_confidence_rules() -> dict

Description
Returns claim confidence labels, behaviors, and forbidden patterns.

Returns

{
  "labels": dict,
  "behavior": dict,
  "forbidden": list
}

Example

confidence = api.get_claim_confidence_rules()


⸻

7) get_memory_promotion_rules() -> dict

Description
Returns memory promotion gate rules.

Returns

{
  "gate1": str,
  "gate2": str,
  "gate3": str,
  "forbidden": list
}

Example

promotion = api.get_memory_promotion_rules()


⸻

8) get_error_message(code: str) -> str

Description
Returns the error message text for a given error code.

Parameters
	•	code — error message identifier

Returns

"Error message string"

Errors
	•	KeyError if the error code does not exist

Example

msg = api.get_error_message("missing_confidence_label")


⸻

Error Semantics
	•	All invalid keys raise KeyError
	•	No API catches or wraps exceptions
	•	Error handling is delegated to the caller

⸻

Immutability Guarantee

All methods return deep copies.

Modifying returned data never affects:
	•	Internal policy state
	•	Future API calls
	•	Other consumers

This is enforced by:
	•	copy.deepcopy(...) in every getter
	•	Idempotency tests in the test suite

⸻

What the API Does NOT Provide
	•	No write access
	•	No mutation helpers
	•	No derived logic
	•	No defaults or fallbacks
	•	No inference

The API is a pure read interface.

⸻

Stability & Versioning
	•	This API contract is bound to SPEC v1.3.2
	•	Any change requires:
	•	Spec version bump
	•	Test updates
	•	Explicit re-lock of STEP 4

⸻

Status
	•	API: Complete
	•	Behavior: Deterministic
	•	Mutability: Forbidden
	•	Spec alignment: Strict