"""Application bootstrap package."""

from functools import lru_cache

from meterweb.bootstrap.container import AppContainer


@lru_cache
def get_container() -> AppContainer:
    return AppContainer.from_env()


__all__ = ["AppContainer", "get_container"]
