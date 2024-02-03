from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Optional

from dashy.sensors import Button, ButtonCallback
from dashy.vendor import asyncpio

if TYPE_CHECKING:
    from dashy.dashy import Dashy

logger = logging.getLogger(__name__)


class GPIOButton(Button):
    def __init__(self, gpio: int) -> None:
        self.settled = False
        self.gpio = gpio
        self.cancel: Optional[Callable[[], Awaitable[None]]] = None
        self.callbacks: list[ButtonCallback] = []

    async def start(self, dashy: Dashy) -> None:
        pi = await dashy.get_service(asyncpio.pi)  # type: ignore

        await pi.set_mode(self.gpio, asyncpio.INPUT)  # type: ignore
        await pi.set_pull_up_down(self.gpio, asyncpio.PUD_UP)  # type: ignore
        callback = await pi.callback(
            self.gpio,
            edge=asyncpio.RISING_EDGE,  # type: ignore
            func=self.emit,
        )
        self.cancel = callback.cancel
        asyncio.get_event_loop().call_later(0.25, self.set_settled)

    def set_settled(self) -> None:
        self.settled = True

    async def stop(self) -> None:
        if self.cancel:
            await self.cancel()
        self.cancel = None

    def register(self, f: ButtonCallback) -> None:
        if f not in self.callbacks:
            self.callbacks.append(f)

    def unregister(self, f: ButtonCallback) -> None:
        if f in self.callbacks:
            self.callbacks.remove(f)

    async def emit(self, _: Any, __: Any, ___: Any) -> None:
        if not self.settled:
            return

        for callback in self.callbacks:
            try:
                await callback()
            except Exception:  # noqa: PERF203
                logger.exception("ButtonCallback failed:")
