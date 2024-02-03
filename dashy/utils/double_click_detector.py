from __future__ import annotations

import asyncio
import logging
from contextlib import suppress
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from dashy.sensors import ButtonCallback

logger = logging.getLogger(__name__)


class DoubleClickDetector:
    def __init__(self, f: Optional[ButtonCallback] = None) -> None:
        self._timeout: Optional[asyncio.Task[None]] = None
        self._single: list[ButtonCallback] = [] if f is None else [f]
        self._double: list[ButtonCallback] = []

    def on_single_click(self, f: ButtonCallback) -> ButtonCallback:
        self._single.append(f)
        return f

    def on_double_click(self, f: ButtonCallback) -> ButtonCallback:
        self._double.append(f)
        return f

    async def __call__(self) -> None:
        async def emit(callbacks: list[ButtonCallback], *, delay: bool = False) -> None:
            if delay:
                await asyncio.sleep(0.5)
                self._timeout = None

            for callback in callbacks:
                try:
                    await callback()
                except Exception:  # noqa: PERF203
                    logger.exception("Click callback failed:")

        if self._timeout is not None:
            self._timeout.cancel()
            with suppress(asyncio.CancelledError):
                await self._timeout
            self._timeout = None
            await emit(self._double)
        elif self._double:
            self._timeout = asyncio.create_task(emit(self._single, delay=True))
        else:
            await emit(self._single)
