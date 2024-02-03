from __future__ import annotations

import asyncio
import math
from contextlib import suppress
from typing import TYPE_CHECKING, Any, Optional, TypeVar, cast

from aiohttp import ClientSession
from playwright.async_api import Browser

from dashy.displays.save_to_disk import SaveToDisk
from dashy.services.aiohttp import AiohttpProvider
from dashy.services.asyncpio import AsyncpioProvider, pi
from dashy.services.playwright import PlaywrightProvider

if TYPE_CHECKING:
    from dashy.dashboards import Dashboard
    from dashy.displays import Display

T = TypeVar("T")


REGISTRY = {
    Browser: PlaywrightProvider(),
    ClientSession: AiohttpProvider(),
    pi: AsyncpioProvider(),
}


class Dashy:
    def __init__(self) -> None:
        self.display: Display = SaveToDisk()
        self.sleep_task: Optional[asyncio.Task[None]] = None
        self.last_dashboard: Optional[Dashboard] = None
        self.started_dashboards: set[Dashboard] = set()
        self.dashboards: list[Dashboard] = []
        self.skip_sleep = False
        self.services: dict[type, Any] = {}

    async def get_service(self, t: type[T]) -> T:
        service = self.services.get(t)
        if service is None:
            provider = REGISTRY[t]
            service = await provider.start()
            self.services[t] = service
        return cast(T, service)

    async def run(self) -> None:
        if self.display is None:
            msg = "No display were configured"
            raise RuntimeError(msg)

        await self.display.start(self)
        await self.render_loop(self.display)

    async def stop(self) -> None:
        for dashboard in self.started_dashboards:
            await dashboard.stop()

        await self.display.stop()

        for t, provider in REGISTRY.items():
            if t in self.services:
                await provider.stop()

    async def render_loop(self, display: Display) -> None:
        self.last_dashboard = None

        while True:
            pause_time = math.inf

            for dashboard in self.dashboards:
                if dashboard not in self.started_dashboards:
                    await dashboard.start(self)
                    self.started_dashboards.add(dashboard)

                result = await dashboard.next(
                    force=self.last_dashboard is not dashboard
                )
                min_interval = dashboard.min_interval
                if min_interval is not None:
                    pause_time = min(pause_time, min_interval)

                if result == "SKIP":
                    continue

                self.last_dashboard = dashboard
                if result is not None:
                    await display.show_image(result)
                break
            else:
                self.last_dashboard = None

            if not self.skip_sleep:
                self.sleep_task = asyncio.create_task(asyncio.sleep(pause_time))
                with suppress(asyncio.CancelledError):
                    await self.sleep_task
                self.sleep_task = None
            else:
                self.skip_sleep = False

    def wakeup(self, *, force: bool = False) -> None:
        if force:
            self.last_dashboard = None

        if self.sleep_task is not None:
            self.sleep_task.cancel()
        else:
            self.skip_sleep = True
