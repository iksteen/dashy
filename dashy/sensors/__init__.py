from abc import ABC, abstractmethod
from typing import Awaitable, Callable

ButtonCallback = Callable[[], Awaitable[None]]


class Button(ABC):
    @abstractmethod
    async def register(self, f: ButtonCallback) -> None:
        ...

    @abstractmethod
    async def unregister(self, f: ButtonCallback) -> None:
        ...
