from __future__ import annotations

import asyncio
import json
import logging
import time
from io import BytesIO
from typing import TYPE_CHECKING, Any, Literal, Union, cast

import aiofiles
import aiohttp
from aiohttp import BasicAuth
from bs4 import BeautifulSoup
from PIL import Image
from playwright.async_api import Browser, Playwright, Route
from playwright.async_api import async_playwright as playwright
from spotifyaio import SpotifyClient, Track

from dashy.dashboards import Dashboard

if TYPE_CHECKING:
    from dashy.displays import Display

logger = logging.getLogger(__name__)

template = """
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
            <h2 id="artist" />
        </footer>
    </body>
</html>
"""


class SpotifyDashboard(Dashboard):
    credentials: dict[str, Any]
    display: Display
    spotify: SpotifyClient
    session: aiohttp.ClientSession
    playwright: Playwright
    browser: Browser

    min_interval = 1.0

    def __init__(self) -> None:
        self.last_track = None

    async def start(self, display: Display) -> None:
        try:
            async with aiofiles.open("spotify-credentials.json") as f:
                self.credentials = json.loads(await f.read())
        except (OSError, ValueError):
            logger.exception("Invalid or missing spotify credentials")
            self.credentials = {}

        self.display = display
        self.session = aiohttp.ClientSession()
        self.spotify = SpotifyClient(
            session=self.session, refresh_token_function=self.get_token
        )
        self.playwright = await playwright().start()
        self.browser = await self.playwright.chromium.launch()

    async def stop(self) -> None:
        await self.browser.close()
        await self.playwright.stop()
        await self.spotify.close()
        await self.session.close()

    async def get_token(self) -> str:
        if self.credentials["expires"] < time.time():
            async with self.session.post(
                "https://accounts.spotify.com/api/token",
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": self.credentials["refresh_token"],
                },
                auth=BasicAuth(
                    self.credentials["client_id"], self.credentials["client_secret"]
                ),
            ) as r:
                if not r.ok:
                    error = await r.text()
                    logger.error("Failed to refresh token: %s", error)
                    self.credentials["access_token"] = ""
                else:
                    credentials = await r.json()
                    self.credentials["expires"] = (
                        time.time() + credentials["expires_in"]
                    )
                    self.credentials["access_token"] = credentials["access_token"]
                    if "refresh_token" in credentials:
                        self.credentials["refresh_token"] = credentials["refresh_token"]

                async with aiofiles.open("spotify-credentials.json", "w") as f:
                    await f.write(json.dumps(self.credentials))

        return cast(str, self.credentials["access_token"])

    async def next(self, *, force: bool) -> Union[Literal["SKIP"], None, Image.Image]:
        if not self.credentials.get("access_token"):
            return "SKIP"

        np = await self.spotify.get_current_playing()
        if np is not None and np.is_playing and np.currently_playing_type == "track":
            if force or np.item.uri != self.last_track:
                image = await self.render_track(
                    np.item,
                )
                self.last_track = np.item.uri
                return image
            return None

        self.last_track = None
        return "SKIP"

    async def render_track(
        self,
        track: Track,
    ) -> Image:
        async def handle_cover(route: Route) -> None:
            if not track.album.images:
                await route.fulfill(status=404)
                return

            async with self.session.get(track.album.images[0].url) as response:
                status = response.status
                data = await response.read()
                content_type = response.headers.get("content-type")

            await route.fulfill(status=status, body=data, content_type=content_type)

        soup = BeautifulSoup(template, "html.parser")
        soup.find(id="title").append(track.name)
        soup.find(id="artist").append(
            ", ".join(artist.name for artist in track.artists)
        )

        width, height = self.display.resolution
        page = await self.browser.new_page(viewport={"width": width, "height": height})
        try:
            await page.route("http://localhost/cover.png", handle_cover)
            await page.set_content(str(soup), wait_until="networkidle")
            image_data = await page.screenshot()
            return Image.open(BytesIO(image_data))
        finally:
            await page.close()


if __name__ == "__main__":
    from dotenv import load_dotenv

    from dashy.displays.save_to_disk import SaveToDisk

    load_dotenv()
    display = SaveToDisk()

    async def main() -> None:
        dashboard = SpotifyDashboard()
        await dashboard.start(display)
        image = await dashboard.next(force=True)
        await display.show_image(image)
        await dashboard.stop()

    asyncio.run(main())
