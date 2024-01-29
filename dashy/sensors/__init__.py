from abc import ABC, abstractmethod
from typing import Awaitable, Callable

ButtonCallback = Callable[[], Awaitable[None]]


class Button(ABC):
    @abstractmethod
    def register(self, f: ButtonCallback) -> None:
        ...

    @abstractmethod
    def unregister(self, f: ButtonCallback) -> None:
        ...

    def __call__(self, f: ButtonCallback) -> ButtonCallback:
        self.register(f)
        return f
