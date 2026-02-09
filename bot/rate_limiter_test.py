import time

# pylint: disable=protected-access

# custom imports
from rate_limiter import RateLimitManager


def now(seconds: int = 0) -> int:
    """
    Get the current time in seconds since the epoch.
    """
    return int(time.time()) + seconds


def test_not_registered_user() -> None:
    """
    Test the RateLimitManager with a user that has not performed any actions.
    """
    rate_limit_manager = RateLimitManager(rate_limit_in_seconds=5)
    user_id = 1
    assert rate_limit_manager.can_perform_action(
        user_id), "User should be able to perform action"


def test_allow_user() -> None:
    rate_limit = 5
    rate_limit_manager = RateLimitManager(rate_limit_in_seconds=rate_limit)
    user_id = 2

    last_action_time = now(-rate_limit)

    # Simulate the user performing an action
    rate_limit_manager.record_action(user_id, last_action_time)

    assert rate_limit_manager.can_perform_action(
        user_id), "User should be able to perform action"


def test_deny_user() -> None:

    rate_limit_manager = RateLimitManager(rate_limit_in_seconds=5)
    user_id = 3

    # Simulate the user performing an action
    rate_limit_manager.record_action(user_id, now())

    can_perform = rate_limit_manager.can_perform_action(user_id)
    if can_perform:
        print("User can perform action")
    else:
        print("Try again at", can_perform.end_time())
        print("Try again in", can_perform._wait_time, "seconds")

    # Simulate the user trying to perform an action again within the rate limit
    assert not rate_limit_manager.can_perform_action(
        user_id), "User should not be able to perform action"


if __name__ == '__main__':
    test_not_registered_user()
    test_allow_user()
    test_deny_user()
    print("All tests passed.")
