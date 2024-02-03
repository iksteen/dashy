from typing import Any, Callable, Awaitable

INPUT: int
PUD_UP: int
RISING_EDGE: int


class Callback:
    async def cancel(self) -> None:
        ...


class pi:
    async def connect(self) -> None:
        ...

    async def stop(self) -> None:
        ...

    async def set_mode(self, gpio: int, mode: Any) -> None:
        ...

    async def set_pull_up_down(self, gpio: int, pud: int) -> None:
        ...

    async def callback(
        self,
        user_gpio: int,
        edge: int,
        func: Callable[[int, int, int], Awaitable[None]],
    ) -> Callback:
        ...
