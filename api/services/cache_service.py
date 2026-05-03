"""Small cache helpers for API MVP."""

from __future__ import annotations

from functools import lru_cache
from typing import Callable, TypeVar

T = TypeVar("T")


def memoized(maxsize: int = 128) -> Callable[[Callable[..., T]], Callable[..., T]]:
    return lru_cache(maxsize=maxsize)

