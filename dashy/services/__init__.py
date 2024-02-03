from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")


class ServiceProvider(Generic[T], metaclass=ABCMeta):
    @abstractmethod
    async def start(self) -> T:
        ...

    @abstractmethod
    async def stop(self) -> None:
        ...
