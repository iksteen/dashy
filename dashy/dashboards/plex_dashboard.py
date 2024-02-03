from __future__ import annotations

import logging
from io import BytesIO
from typing import TYPE_CHECKING, Literal, Optional, Union, cast
from xml.etree.ElementTree import Element

import aiohttp
from bs4 import BeautifulSoup
from defusedxml.ElementTree import fromstring as parse_xml
from PIL import Image
from playwright.async_api import Browser, Route

from dashy.dashboards import Dashboard

if TYPE_CHECKING:
    from dashy.dashy import Dashy
    from dashy.displays import Display

logger = logging.getLogger(__name__)

DEFAULT_TEMPLATE = """
<html>
    <head>
        <style type="text/css">
            body {
                width: 100%;
                height: 100%;
                margin: 0px;
                background-image: url("http://localhost/cover.png");
                background-size: cover;
                background-position: center center;
                font-family: sans-serif;
            }

            h1, h2 {
                width: 100%;
                margin: 0;
                color: white;
                text-shadow: 5px 5px #1c171c;
            }

            h1 {
                font-size: 10vh;
            }

            h2 {
                font-size: 7vh;
            }

            footer {
                padding: 0 0 2.5vh 5vw;
                position: absolute;
                bottom: 0;
                left: 0;
                right: 0;
            }
        </style>
    </head>
    <body>
        <footer>
            <h1 id="title" />
            <h2 id="series" />
        </footer>
    </body>
</html>
"""


class PlexDashboard(Dashboard):
    display: Display
    session: aiohttp.ClientSession
    browser: Browser

    min_interval = 1

    def __init__(  # noqa: PLR0913
        self,
        *,
        server: str,
        token: str,
        user: Optional[str] = None,
        interval: int = 1,
        template: str = DEFAULT_TEMPLATE,
    ) -> None:
        self.server = server
        self.token = token
        self.user: Optional[str] = user
        self.min_interval = interval
        self.template = template
        self.last_id: Optional[str] = None

    async def start(self, dashy: Dashy) -> None:
        self.display = dashy.display
        self.browser = await dashy.get_service(Browser)
        self.session = await dashy.get_service(aiohttp.ClientSession)

    async def stop(self) -> None:
        pass

    def get_plex_url(self, endpoint: str) -> str:
        return f"{self.server}{endpoint}?X-Plex-Token={self.token}"

    async def request(
        self,
        endpoint: str,
    ) -> Optional[Element]:
        try:
            async with await self.session.request(
                "GET",
                self.get_plex_url(endpoint),
                headers={
                    "Accept": "application/xml",
                },
            ) as r:
                body = await r.text()
                if not r.ok:
                    logger.error("Failed to contact plex: %s %s", r.status, body)
                    return None

                return cast(Element, parse_xml(body))
        except Exception:
            logger.exception("Failed to contact Plex server:")
            return None

    async def next(self, *, force: bool) -> Union[Literal["SKIP"], None, Image.Image]:
        sessions = await self.request("/status/sessions")
        if sessions is None:
            self.last_id = None
            return "SKIP"

        for session in sessions:
            player = session.find("Player")
            user = session.find("User")
            if (
                player
                and player.get("state") == "playing"
                and user
                and user.get("title") == self.user
            ):
                break
        else:
            self.last_id = None
            return "SKIP"

        guid = session.get("guid")
        if force or guid != self.last_id:
            image = await self.render_item(session)
            self.last_id = guid
            return image
        return None

    async def render_item(
        self,
        session: Element,
    ) -> Image:
        async def handle_cover(route: Route) -> None:
            art = session.get("art")
            if art is not None:
                image_url = self.get_plex_url(art)
                async with self.session.get(image_url) as r:
                    status = r.status
                    data = await r.read()
                    content_type = r.headers.get("content-type")

                await route.fulfill(status=status, body=data, content_type=content_type)
            else:
                await route.fulfill(status=404)

        title = session.get("title")

        series = None
        if session.get("type") == "episode":
            series_title = session.get("grandparentTitle")
            season_index = session.get("parentIndex")
            episode_index = session.get("index")
            if series_title is not None:
                if season_index is not None and episode_index is not None:
                    series = f"{series_title} - S{int(season_index):02}E{int(episode_index):02}"
                else:
                    series = series_title

        soup = BeautifulSoup(self.template, "html.parser")
        soup.find(id="title").append(title)
        if series:
            soup.find(id="series").append(series)
        else:
            soup.find(id="series").decompose()

        width, height = self.display.resolution
        page = await self.browser.new_page(viewport={"width": width, "height": height})
        try:
            await page.route("http://localhost/cover.png", handle_cover)
            await page.set_content(str(soup), wait_until="networkidle")
            image_data = await page.screenshot()
            return Image.open(BytesIO(image_data))
        finally:
            await page.close()
