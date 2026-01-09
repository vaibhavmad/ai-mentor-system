# Pacing Controller – Orchestrator Integration Contract (LOCKED)

This document defines the ONLY allowed way to use the Pacing Controller.

Any deviation is a violation.

---

## Ownership Rules (Non-Negotiable)

The Pacing Controller is the single enforcement authority for:
- Token budgets
- Hard caps
- Multi-turn behavior

The Orchestrator:
- Selects pacing mode
- Calls pacing APIs
- Reacts to pacing decisions

The Orchestrator NEVER:
- Counts tokens
- Enforces caps
- Decides continuation
- Overrides pacing decisions

---

## Mandatory Call Order

The ONLY valid execution flow:

1. Orchestrator selects `PacingMode`
2. Orchestrator calls `prepare_request(mode)`
3. LLM Executor generates output using `max_tokens`
4. Orchestrator calls `evaluate_output(mode, output_text)`
5. Orchestrator reacts to `PacingDecision`

Any skipped or reordered call is invalid.

---

## Reaction Rules

- `TokenLimitExceededError` → reject output immediately
- `must_continue_in_next_turn = True` → continue next turn
- `must_continue_in_next_turn = False` → stop

No retries, truncation, or overrides are permitted.

---

## Deliberative Reset Responsibility

- `deliberative_turn_count` is NOT reset by the Pacing Controller
- Orchestrator MUST reset it when the session ends

---

## Bypass Prohibitions

The following are explicitly forbidden:
- Generating output without calling `prepare_request`
- Modifying `max_tokens`
- Skipping `evaluate_output`
- Counting tokens outside Pacing Controller

---

This contract is LOCKED.
Changes require architecture review.