import asyncio
import importlib
import math
import os

from dotenv import load_dotenv

from dashy.dashboards.slideshow_dashboard import SlideshowDashboard
from dashy.dashboards.spotify_dashboard import SpotifyDashboard
from dashy.displays import Display

DASHBOARDS = [SpotifyDashboard(), SlideshowDashboard()]


async def main(display: Display) -> None:
    dashboards = []

    try:
        for dashboard in DASHBOARDS:
            await dashboard.start(display)
            dashboards.append(dashboard)

        last_dashboard = None

        while True:
            pause_time = math.inf

            for dashboard in dashboards:
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
        for dashboard in reversed(dashboards):
            await dashboard.stop()


if __name__ == "__main__":
    load_dotenv()

    display_path = os.environ.get("DASHY_DISPLAY", "dashy.displays.inky_auto.InkyAuto")
    display_module_name, display_class_name = display_path.rsplit(".", 1)
    display_module = importlib.import_module(display_module_name)
    display_class = getattr(display_module, display_class_name)
    display = display_class()

    asyncio.run(main(display))
