from datetime import timedelta


class FakeClock:
    """
    Deterministic fake clock for tests.

    Public API only:
    - now (current time)
    - advance_days(days)
    """

    def __init__(self, start_date):
        self.now = start_date

    def advance_days(self, days: int):
        self.now += timedelta(days=days)