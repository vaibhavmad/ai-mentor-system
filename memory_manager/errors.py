class InvalidContextError(ValueError):
    pass


class ConflictUnresolvedError(RuntimeError):
    pass


class PromotionError(RuntimeError):
    pass


class DecayReconfirmationRequired(RuntimeError):
    pass