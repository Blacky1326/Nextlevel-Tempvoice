import time
from dataclasses import dataclass


@dataclass
class RateLimitResponse:
    _can_perform_action: bool
    _wait_time: int = 0

    def __bool__(self) -> bool:
        return self._can_perform_action

    def end_time(self) -> int:
        return int(time.time()) + self._wait_time


class RateLimitManager:
    '''
    This class is used to manage the rate limit for users.
    An instance of this class is bound to the client.
    '''

    def __init__(
        self,
        rate_limit_in_seconds: int = 5,
    ):
        self.rate_limit = rate_limit_in_seconds
        self.user_last_action: dict[int, int] = {}

    def record_action(
        self,
        user_id: int,
        current_time: int = None
    ) -> None:
        if current_time is None:
            current_time = int(time.time())
        self.user_last_action[user_id] = current_time

    def can_perform_action(self, user_id: int) -> RateLimitResponse:
        # Check if the user is in the rate limit dictionary
        if user_id not in self.user_last_action:
            return RateLimitResponse(True)

        # Check if the user is within the rate limit
        now = int(time.time())
        last_action = self.user_last_action[user_id]

        if now - last_action >= self.rate_limit:
            return RateLimitResponse(True)

        # User is still within the rate limit
        remaining_time = self.rate_limit - (now - last_action)
        return RateLimitResponse(
            False,
            remaining_time,
        )
