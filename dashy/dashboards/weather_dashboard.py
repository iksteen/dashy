from __future__ import annotations

import time
from io import BytesIO
from typing import TYPE_CHECKING, Literal, Optional, Union

from PIL import Image
from playwright.async_api import Browser, Playwright
from playwright.async_api import async_playwright as playwright

from dashy.dashboards import Dashboard
from dashy.utils.resize_image import resize_image

if TYPE_CHECKING:
    from dashy.displays import Display

TEMPLATE_AUTO = """<div id="ww_015d9fd14a2fa" v='1.3' loc='auto' a='{"t":"horizontal","lang":"en","sl_lpl":1,"ids":[],"font":"Arial","sl_ics":"one","sl_sot":"celsius","cl_bkg":"image","cl_font":"#FFFFFF","cl_cloud":"#FFFFFF","cl_persp":"#81D4FA","cl_sun":"#FFC107","cl_moon":"#FFC107","cl_thund":"#FF5722"}'><a href="https://weatherwidget.org/" id="ww_015d9fd14a2fa_u" target="_blank">HTML Weather Widget for website</a></div><script async src="https://app2.weatherwidget.org/js/?id=ww_015d9fd14a2fa"></script>"""
TEMPLATE_LOC = """<div id="ww_17a90a88b8155" v='1.3' loc='id' a='{"t":"horizontal","lang":"en","sl_lpl":1,"ids":["***LOCATION***"],"font":"Arial","sl_ics":"one_a","sl_sot":"celsius","cl_bkg":"image","cl_font":"#FFFFFF","cl_cloud":"#FFFFFF","cl_persp":"#81D4FA","cl_sun":"#FFC107","cl_moon":"#FFC107","cl_thund":"#FF5722"}'>More forecasts: <a href="https://oneweather.org/amsterdam/30_days/" id="ww_17a90a88b8155_u" target="_blank">Weather forecast Amsterdam 30 days</a></div><script async src="https://app2.weatherwidget.org/js/?id=ww_17a90a88b8155"></script>"""


class WeatherDashboard(Dashboard):
    display: Display
    playwright: Playwright
    browser: Browser

    def __init__(self, *, location: Optional[str] = None, interval: int = 3600) -> None:
        if location:
            self.template = TEMPLATE_LOC.replace("***LOCATION***", location)
        else:
            self.template = TEMPLATE_AUTO
        self.interval = interval

        self.next_update: Optional[int] = None

    async def start(self, display: Display) -> None:
        self.display = display
        self.playwright = await playwright().start()
        self.browser = await self.playwright.chromium.launch()

    async def stop(self) -> None:
        await self.browser.close()
        await self.playwright.stop()

    @property
    def min_interval(self) -> Optional[int]:
        if self.next_update is None:
            return 0

        return max(0, self.next_update - int(time.time()))

    async def next(self, *, force: bool) -> Union[Literal["SKIP"], None, Image.Image]:
        now = int(time.time())

        if not (force or self.next_update is None or self.next_update < now):
            return None

        self.next_update = now - now % self.interval + self.interval

        width, height = self.display.resolution
        page = await self.browser.new_page(viewport={"width": width, "height": height})
        try:
            await page.set_content(self.template, wait_until="networkidle")
            image_data = await page.locator(".ww-box").screenshot(
                style=".ww_source, .ww_arr { display: none !important }"
            )
            im = Image.open(BytesIO(image_data))
            try:
                return resize_image(im, self.display.resolution, mode="COVER")
            finally:
                im.close()
        finally:
            await page.close()
