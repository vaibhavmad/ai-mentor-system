from dataclasses import dataclass
from typing import Optional, Literal, Dict, List

from pacing_controller.enums import PacingMode


# ---------------------------------------------------------------------
# SESSION STATE
# ---------------------------------------------------------------------

@dataclass
class SessionState:
    """
    Mutable session state owned exclusively by the Orchestrator.

    This tracks conversation progress across turns.
    """
    session_id: str
    turn_index: int = 0
    mode: Optional[PacingMode] = None
    user_choice: Optional[str] = None
    deliberative_turn_count: int = 0
    active_context: Optional[str] = None


# ---------------------------------------------------------------------
# ROUTE RESPONSE MODELS (IMMUTABLE, NON-PRESENTATIONAL)
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class IntakeResponse:
    """
    Returned by the INTAKE route.

    Contains only structured intake questions.
    Rendering is handled by the caller / UI.
    """
    type: Literal["INTAKE"]
    questions: List[str]


@dataclass(frozen=True)
class GroundingResponse:
    """
    Returned by the GROUNDING route.

    Always contains exactly 5 grounding questions.
    """
    type: Literal["GROUNDING"]
    reason: str
    questions: List[str]  # MUST always be length == 5


@dataclass(frozen=True)
class UserChoicePrompt:
    """
    Returned by the USER_CHOICE route (turn 1).

    Presents A/B/C options without mutating session state.
    """
    type: Literal["USER_CHOICE"]
    options: Dict[str, str]  # {"A": "...", "B": "...", "C": "..."}


    # ------------------------------------------------------------------
# ORCHESTRATOR CONTEXT (SHARED CONTRACT)
# ------------------------------------------------------------------

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class OrchestratorContext:
    """
    Immutable context object passed to OutputValidator.

    HARD RULES:
    - No logic
    - No validation
    - No side effects
    - Pure data contract only
    """

    uncertainty_level: Any
    memory_write_attempted: bool
    memory_confirmation_asked: bool
    memory_scope: Any
    token_count: int
    token_limit: int
    user_intent: Any
    assumptions_required: bool
    contains_medium_or_low_confidence_claims: bool