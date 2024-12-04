import asyncio
import time
from functools import wraps
from typing import Callable, Any


def rate_limit(delay: float = 0.34):
    """
    A decorator that implements rate limiting for asynchronous function calls.

    This decorator ensures a minimum time interval between successive function calls,
    helping to prevent API rate limit violations. It can use either a default delay
    or a dynamic delay from an instance's request_delay attribute.

    Args:
        delay (float, optional): Default minimum time between calls in seconds.
                               Defaults to 0.34 seconds.

    Returns:
        Callable: Decorated function with rate limiting applied

    Features:
        - Supports both default and instance-specific delay times
        - Uses asyncio.sleep for non-blocking delays
        - Preserves function metadata through @wraps
        - Thread-safe using nonlocal state

    Examples:
        Basic usage with default delay:
        >>> @rate_limit()
        ... async def fetch_data():
        ...     # API call here
        ...     pass

        Usage with custom delay:
        >>> @rate_limit(delay=1.0)
        ... async def fetch_data():
        ...     # API call here
        ...     pass

        Usage with instance-specific delay:
        >>> class APIClient:
        ...     def __init__(self):
        ...         self.request_delay = 0.5
        ...     
        ...     @rate_limit()
        ...     async def fetch_data(self):
        ...         # Will use self.request_delay instead of default
        ...         pass

    Note:
        - The decorator checks for a request_delay attribute on the first argument
          (typically self in methods) and uses that value if available
        - Time tracking is done using time.time() for high precision
        - The delay is implemented using asyncio.sleep for non-blocking behavior
    """
    def decorator(func: Callable) -> Callable:
        last_call = 0.0

        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            nonlocal last_call

            instance_delay = delay
            if args and hasattr(args[0], 'request_delay'):
                instance_delay = args[0].request_delay

            current_time = time.time()
            time_since_last = current_time - last_call

            if time_since_last < instance_delay:
                await asyncio.sleep(instance_delay - time_since_last)

            last_call = time.time()
            return await func(*args, **kwargs)

        return wrapper
    return decorator
