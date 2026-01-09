from dataclasses import dataclass
from enum import Enum
from typing import Optional, Literal


class ErrorCode(Enum):
    missingconfidencelabel = "missingconfidencelabel"
    lowconfidenceasserted = "lowconfidenceasserted"
    percentageinchoice = "percentageinchoice"
    invaliduserchoiceformat = "invaliduserchoiceformat"
    assumptionsnotsurfaced = "assumptionsnotsurfaced"
    proceededwithuncertainty3 = "proceededwithuncertainty3"
    proceededwithuncertainty45 = "proceededwithuncertainty45"
    memorywritewithoutconfirmation = "memorywritewithoutconfirmation"
    memorywithoutscope = "memorywithoutscope"
    tokencapreached = "tokencapreached"
    nextstepsnotclear = "nextstepsnotclear"
    uncertaintynotdisclosed = "uncertaintynotdisclosed"
    intentnotaddressed = "intentnotaddressed"
    forbiddenauthoritativephrasing = "forbiddenauthoritativephrasing"


@dataclass(frozen=True)
class ValidationResult:
    status: Literal["ACCEPTED", "REJECTED"]
    error_code: Optional[ErrorCode]
    message: Optional[str]

    def __post_init__(self):
        # Enforce invariant:
        # error_code is None ONLY if status == "ACCEPTED"
        if self.status == "ACCEPTED" and self.error_code is not None:
            raise ValueError(
                "ValidationResult with status ACCEPTED must not have an error_code"
            )

        if self.status == "REJECTED" and self.error_code is None:
            raise ValueError(
                "ValidationResult with status REJECTED must have an error_code"
            )