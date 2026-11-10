"""Типізований декоратор вимірювання без зміни сигнатури функції."""

import logging
import time
from collections.abc import Callable
from functools import wraps
from typing import ParamSpec, TypeVar

P = ParamSpec("P")
T = TypeVar("T")
logger = logging.getLogger(__name__)


def timed(function: Callable[P, T]) -> Callable[P, T]:
    @wraps(function)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        started = time.perf_counter()
        try:
            return function(*args, **kwargs)
        finally:
            logger.info(
                "%s elapsed_ms=%.6f", function.__name__, (time.perf_counter() - started) * 1000
            )

    return wrapper
