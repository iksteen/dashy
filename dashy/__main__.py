from __future__ import annotations

import asyncio
import logging
import math
import sys
from contextlib import suppress
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

from dotenv import load_dotenv

if TYPE_CHECKING:
    from dashy.dashboards import Dashboard
    from dashy.displays import Display


class Dashy:
    def __init__(self) -> None:
        self.display: Optional[Display] = None
        self.sleep_task: Optional[asyncio.Task[None]] = None
        self.last_dashboard: Optional[Dashboard] = None
        self.dashboards: list[Dashboard] = []

    async def run(self) -> None:
        if self.display is None:
            msg = "No display were configured"
            raise RuntimeError(msg)

        await self.display.start()
        try:
            await self.render_loop(self.display)
        finally:
            await self.display.stop()

    async def render_loop(self, display: Display) -> None:
        started_dashboards = []
        try:
            self.last_dashboard = None

            while True:
                pause_time = math.inf

                for dashboard in self.dashboards:
                    if dashboard not in started_dashboards:
                        await dashboard.start(display)
                        started_dashboards.append(dashboard)

                    pause_time = min(pause_time, dashboard.min_interval)
                    result = await dashboard.next(
                        force=self.last_dashboard is not dashboard
                    )
                    if result == "SKIP":
                        continue

                    self.last_dashboard = dashboard
                    if result is not None:
                        await display.show_image(result)
                    break
                else:
                    self.last_dashboard = None

                self.sleep_task = asyncio.create_task(asyncio.sleep(pause_time))
                with suppress(asyncio.CancelledError):
                    await self.sleep_task
                self.sleep_task = None

        finally:
            for dashboard in reversed(started_dashboards):
                await dashboard.stop()

    def wakeup(self, *, force: bool = False) -> None:
        if force:
            self.last_dashboard = None

        if self.sleep_task is not None:
            self.sleep_task.cancel()


if __name__ == "__main__":
    load_dotenv()

    dashy = Dashy()

    config_path = sys.argv[1] if len(sys.argv) > 1 else "conf.py"
    with Path(config_path).open("r") as f:
        content = f.read()
    conf_globals: dict[str, Any] = {"DASHY": dashy}
    exec(content, conf_globals)

    loglevel = conf_globals.get("LOGLEVEL", logging.INFO)
    logging.basicConfig(level=loglevel)

    asyncio.run(dashy.run())
