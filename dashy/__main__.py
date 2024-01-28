from __future__ import annotations

import asyncio
import logging
import math
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

from dotenv import load_dotenv

if TYPE_CHECKING:
    from dashy.dashboards import Dashboard
    from dashy.displays import Display


async def main(display: Display, dashboards: list[Dashboard]) -> None:
    try:
        await display.start()

        started_dashboards = []
        try:
            last_dashboard = None

            while True:
                pause_time = math.inf

                for dashboard in dashboards:
                    if dashboard not in started_dashboards:
                        await dashboard.start(display)
                        started_dashboards.append(dashboard)

                    pause_time = min(pause_time, dashboard.min_interval)
                    result = await dashboard.next(force=last_dashboard is not dashboard)
                    if result == "SKIP":
                        continue

                    last_dashboard = dashboard
                    if result is not None:
                        await display.show_image(result)
                    break
                else:
                    last_dashboard = None

                await asyncio.sleep(pause_time)

        finally:
            for dashboard in reversed(started_dashboards):
                await dashboard.stop()
    finally:
        await display.stop()


if __name__ == "__main__":
    load_dotenv()

    config_path = sys.argv[1] if len(sys.argv) > 1 else "conf.py"
    with Path(config_path).open("r") as f:
        content = f.read()
    conf_globals: dict[str, Any] = {}
    exec(content, conf_globals)

    loglevel = conf_globals.get("LOGLEVEL", logging.INFO)
    logging.basicConfig(level=loglevel)

    display = conf_globals["DISPLAY"]
    dashboards = conf_globals["DASHBOARDS"]

    asyncio.run(main(display, dashboards))
