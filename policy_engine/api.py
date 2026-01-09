import copy


class PolicyAPI:
    def __init__(self, policy: dict):
        self._policy = policy

    def get_token_limits(self, mode: str) -> dict:
        return copy.deepcopy(self._policy["pacing"]["modes"][mode])

    def get_uncertainty_matrix(self) -> dict:
        return copy.deepcopy(self._policy["uncertainty"])

    def get_user_choice_template(self) -> dict:
        return copy.deepcopy(self._policy["userchoice"])

    def get_grounding_questions(self, context: str) -> list:
        return copy.deepcopy(
            self._policy["groundingprotocol"]["questions"][context]
        )

    def get_output_validation_rules(self) -> dict:
        return copy.deepcopy(self._policy["outputvalidation"])

    def get_claim_confidence_rules(self) -> dict:
        return copy.deepcopy(self._policy["claim_confidence"])

    def get_memory_promotion_rules(self) -> dict:
        return copy.deepcopy(self._policy["memory"]["promotion"])

    def get_error_message(self, code: str) -> str:
        return copy.deepcopy(self._policy["error_messages"][code])