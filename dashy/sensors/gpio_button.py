from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable, Optional

from dashy.sensors import Button, ButtonCallback
from dashy.vendor import asyncpio

logger = logging.getLogger(__name__)


class GPIOButton(Button):
    pi: Optional[asyncpio.pi] = None  # type: ignore

    def __init__(self, gpio: int) -> None:
        self.gpio = gpio
        self.cancel: Optional[Callable[[], Awaitable[None]]] = None
        self.callbacks: list[ButtonCallback] = []

    async def start(self) -> None:
        if GPIOButton.pi is None:
            GPIOButton.pi = asyncpio.pi()  # type: ignore
            await GPIOButton.pi.connect()

        await GPIOButton.pi.set_mode(self.gpio, asyncpio.INPUT)  # type: ignore
        await GPIOButton.pi.set_pull_up_down(self.gpio, asyncpio.PUD_UP)  # type: ignore
        callback = await GPIOButton.pi.callback(
            self.gpio,
            edge=asyncpio.RISING_EDGE,  # type: ignore
            func=self.emit,
        )
        self.cancel = callback.cancel

    async def stop(self) -> None:
        if self.cancel:
            await self.cancel()
        self.cancel = None

    def register(self, f: Callable[[], Awaitable[None]]) -> None:
        if f not in self.callbacks:
            self.callbacks.append(f)

    def unregister(self, f: ButtonCallback) -> None:
        if f in self.callbacks:
            self.callbacks.remove(f)

    async def emit(self, _: Any, __: Any, ___: Any) -> None:
        for callback in self.callbacks:
            try:
                await callback()
            except Exception:  # noqa: PERF203
                logger.exception("ButtonCallback failed:")
