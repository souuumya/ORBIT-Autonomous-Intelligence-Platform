from __future__ import annotations

import asyncio
import inspect
import logging
import random
from typing import Any, Callable, Type, TypeVar


logger = logging.getLogger(__name__)

T = TypeVar("T")


async def async_retry_with_backoff(
    func: Callable[[], Any],
    max_retries: int = 3,
    initial_backoff: float = 0.1,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    retry_exceptions: tuple[Type[Exception], ...] = (Exception,),
    on_retry_callback: Callable[[Exception, int], None] | None = None,
) -> Any:
    """Execute an async callable with exponential backoff and jitter retry logic.

    Args:
        func: The async callable zero-argument function to execute.
        max_retries: Maximum number of retry attempts allowed after initial failure.
        initial_backoff: Initial delay in seconds before first retry.
        backoff_factor: Multiplier applied to backoff delay after each failed attempt.
        jitter: Whether to add random jitter (0 to 50% of delay) to backoff delay.
        retry_exceptions: Tuple of exception classes that trigger a retry attempt.
        on_retry_callback: Optional callback invoked on each retry attempt.

    Returns:
        Result of successful func execution.

    Raises:
        Exception: Re-raises the last caught exception when max_retries is exceeded.
    """
    attempt = 0
    current_backoff = initial_backoff

    while True:
        try:
            if inspect.iscoroutinefunction(func):
                return await func()
            res = func()

            if asyncio.iscoroutine(res):
                return await res
            return res
        except retry_exceptions as exc:
            attempt += 1
            if attempt > max_retries:
                logger.error("Exceeded maximum retries (%d/%d): %s", attempt - 1, max_retries, exc)
                raise exc

            delay = current_backoff
            if jitter:
                delay += random.uniform(0, 0.5 * current_backoff)

            logger.warning(
                "Attempt %d/%d failed: %s. Retrying in %.2fs...",
                attempt,
                max_retries + 1,
                exc,
                delay,
            )

            if on_retry_callback:
                try:
                    on_retry_callback(exc, attempt)
                except Exception as cb_exc:
                    logger.warning("Retry callback raised exception: %s", cb_exc)

            await asyncio.sleep(delay)
            current_backoff *= backoff_factor
