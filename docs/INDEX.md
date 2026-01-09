Documentation Index

This directory contains all authoritative documentation for the AI Mentor System.
If something is not documented here, it should be considered non-binding.

📘 Core Documents
	•	README.md
	•	High-level overview of the system
	•	How to run, test, and validate the project
	•	Entry point for new contributors
	•	SPEC.md
	•	Frozen, system-wide specification
	•	Defines what the system must do
	•	Any violation → system must refuse to operate
	•	API.md
	•	Public API contracts
	•	Read-only guarantees
	•	Error behavior and usage examples

📄 Cross-Module Contracts

These documents define behavioral contracts between multiple modules.
They are architectural agreements, not implementation details.
	•	pacing_orchestrator_contract.md
	•	Contract between pacing controller and orchestrator
	•	Token limits, escalation rules, and pacing modes
	•	(future) memory_manager_contract.md
	•	Memory lifecycle, promotion, decay, and conflict guarantees
	•	(future) output_validator_contract.md
	•	Output validation responsibilities and enforcement rules
	•	(future) llm_executor_contract.md
	•	LLM execution boundaries, adapter responsibilities, and failure modes

🧭 How to Use This Documentation
	•	Start with README.md if you are new
	•	Treat SPEC.md as the source of truth
	•	Refer to API.md when consuming system APIs
	•	Refer to contract documents when working across modules

🔒 Change Policy
	•	Changes to SPEC.md or contract files require:
	•	Explicit approval
	•	Version bump
	•	Corresponding test updates
	•	Documentation drift is treated as a system risk

✅ Status
	•	STEP 4 documentation: Complete
	•	Documentation structure: Locked
	•	All future docs must be added here and indexed