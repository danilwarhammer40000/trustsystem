from contextlib import contextmanager
from filelock import FileLock

from services.user_service import (
    activate_trial,
    activate_paid,
    extend_user,
    get_user,
    create_user
)

from core.sync import full_sync

LOCK_PATH = "/opt/trustsystem/storage/control.lock"
lock = FileLock(LOCK_PATH, timeout=20)


@contextmanager
def control_lock():
    with lock:
        yield


def activate_paid_plan(username: str, plan: str):
    with control_lock():

        if plan == "30":
            user = activate_paid(username, 30)

        elif plan == "60":
            user = activate_paid(username, 60)

        else:
            raise ValueError(f"INVALID_PLAN: {plan}")

    # sync OUTSIDE lock (важно!)
    full_sync()

    return user


def activate_trial_plan(username: str):
    with control_lock():
        user = activate_trial(username)

    full_sync()
    return user


def extend_plan(username: str, days: int):
    with control_lock():
        user = extend_user(username, days)

    full_sync()
    return user


def ensure_user(username: str, tg_id: int):
    with control_lock():
        user = get_user(username)

        if user:
            return user

        user = create_user(username=username, tg_id=tg_id)

    full_sync()
    return user