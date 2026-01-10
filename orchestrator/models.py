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