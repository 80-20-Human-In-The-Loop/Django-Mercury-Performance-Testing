"""Thread safety utilities for the Performance Testing Framework

This module provides thread-safe wrappers and utilities to ensure
the framework works correctly in multi-threaded environments.
"""

import threading
from contextlib import contextmanager
from typing import TypeVar, Generic, Optional, Callable, Any, List, Tuple, Dict
from functools import wraps

from .logging_config import get_logger

logger = get_logger("thread_safety")

T = TypeVar("T")


class ThreadSafeCounter:
    """Thread-safe counter implementation."""

    def __init__(self, initial_value: int = 0):
        """Initialize the counter with an optional initial value."""
        self._value = initial_value
        self._lock = threading.Lock()

    def increment(self, amount: int = 1) -> int:
        """Increment the counter and return the new value."""
        with self._lock:
            self._value += amount
            return self._value

    def decrement(self, amount: int = 1) -> int:
        """Decrement the counter and return the new value."""
        with self._lock:
            self._value -= amount
            return self._value

    @property
    def value(self) -> int:
        """Get the current value of the counter."""
        with self._lock:
            return self._value

    def reset(self, value: int = 0) -> None:
        """Reset the counter to a specific value."""
        with self._lock:
            self._value = value


class ThreadSafeDict(Generic[T]):
    """Thread-safe dictionary wrapper."""

    def __init__(self):
        """Initialize the thread-safe dictionary."""
        self._dict: Dict[str, T] = {}
        self._lock = threading.RLock()  # Use RLock for re-entrant locking

    def get(self, key: str, default: Optional[T] = None) -> Optional[T]:
        """Get a value from the dictionary."""
        with self._lock:
            return self._dict.get(key, default)

    def set(self, key: str, value: T) -> None:
        """Set a value in the dictionary."""
        with self._lock:
            self._dict[key] = value

    def delete(self, key: str) -> bool:
        """Delete a key from the dictionary. Returns True if key existed."""
        with self._lock:
            if key in self._dict:
                del self._dict[key]
                return True
            return False

    def clear(self) -> None:
        """Clear all items from the dictionary."""
        with self._lock:
            self._dict.clear()

    def items(self) -> List[Tuple[str, T]]:
        """Get a copy of all items in the dictionary."""
        with self._lock:
            return list(self._dict.items())

    def keys(self) -> List[str]:
        """Get a copy of all keys in the dictionary."""
        with self._lock:
            return list(self._dict.keys())

    def values(self) -> List[T]:
        """Get a copy of all values in the dictionary."""
        with self._lock:
            return list(self._dict.values())

    def __contains__(self, key: str) -> bool:
        """Check if a key exists in the dictionary."""
        with self._lock:
            return key in self._dict

    def __len__(self) -> int:
        """Get the number of items in the dictionary."""
        with self._lock:
            return len(self._dict)


class ThreadLocalStorage(Generic[T]):
    """Thread-local storage wrapper for thread-specific data."""

    def __init__(self, factory: Optional[Callable[[], T]] = None):
        """
        Initialize thread-local storage.

        Args:
            factory: Optional factory function to create default values.
        """
        self._local = threading.local()
        self._factory = factory
        self._lock = threading.Lock()

    def get(self) -> Optional[T]:
        """Get the value for the current thread."""
        if not hasattr(self._local, "value"):
            if self._factory:
                with self._lock:
                    # Double-check after acquiring lock
                    if not hasattr(self._local, "value"):
                        self._local.value = self._factory()
            else:
                return None
        return getattr(self._local, "value", None)

    def set(self, value: T) -> None:
        """Set the value for the current thread."""
        self._local.value = value

    def clear(self) -> None:
        """Clear the value for the current thread."""
        if hasattr(self._local, "value"):
            delattr(self._local, "value")


@contextmanager
def thread_safe_operation(lock: threading.Lock, timeout: Optional[float] = None):
    """
    Context manager for thread-safe operations with optional timeout.

    Args:
        lock: The lock to acquire.
        timeout: Optional timeout in seconds for acquiring the lock.

    Raises:
        TimeoutError: If the lock cannot be acquired within the timeout.
    """
    acquired = False
    try:
        if timeout is None:
            acquired = lock.acquire()
        else:
            acquired = lock.acquire(timeout=timeout)
        if not acquired:
            raise TimeoutError(f"Could not acquire lock within {timeout} seconds")
        yield
    finally:
        if acquired:
            lock.release()


def synchronized(lock_attr: str = "_lock"):
    """
    Decorator to synchronize method calls using an instance lock.

    Args:
        lock_attr: Name of the lock attribute on the instance.

    Example:
        class MyClass:
            def __init__(self):
                self._lock = threading.Lock()

            @synchronized()
            def my_method(self):
                # This method is thread-safe
                pass
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            lock = getattr(self, lock_attr, None)
            if lock is None:
                logger.warning(
                    f"No lock attribute '{lock_attr}' found on {self.__class__.__name__}"
                )
                return func(self, *args, **kwargs)

            with lock:
                return func(self, *args, **kwargs)

        return wrapper

    return decorator


class SingletonMeta(type):
    """
    Thread-safe Singleton metaclass.

    Usage:
        class MySingleton(metaclass=SingletonMeta):
            pass
    """

    _instances = {}
    _lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            with cls._lock:
                # Double-check locking pattern
                if cls not in cls._instances:
                    instance = super().__call__(*args, **kwargs)
                    cls._instances[cls] = instance
        return cls._instances[cls]


# Global thread-safe counters for the framework
query_counter = ThreadSafeCounter()
cache_hit_counter = ThreadSafeCounter()
cache_miss_counter = ThreadSafeCounter()
active_monitors = ThreadSafeDict[Any]()


def reset_global_counters():
    """Reset all global thread-safe counters."""
    query_counter.reset()
    cache_hit_counter.reset()
    cache_miss_counter.reset()
    active_monitors.clear()
    logger.info("Global thread-safe counters reset")
