from __future__ import annotations

import json
import logging
import time
from io import BytesIO
from typing import TYPE_CHECKING, Any, Literal, Optional, Union, cast

import aiofiles
import aiohttp
from aiohttp import BasicAuth
from bs4 import BeautifulSoup
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
            <h2 id="artist" />
        </footer>
    </body>
</html>
"""


class SpotifyDashboard(Dashboard):
    credentials: dict[str, Any]
    display: Display
    session: aiohttp.ClientSession
    browser: Browser

    min_interval = 1

    def __init__(
        self,
        *,
        credentials: str = "spotify-credentials.json",
        interval: int = 1,
        template: str = DEFAULT_TEMPLATE,
    ) -> None:
        self.credential_path = credentials
        self.min_interval = interval
        self.template = template
        self.last_id = None

    async def start(self, dashy: Dashy) -> None:
        try:
            async with aiofiles.open(self.credential_path) as f:
                self.credentials = json.loads(await f.read())
        except (OSError, ValueError):
            logger.exception("Invalid or missing spotify credentials")
            self.credentials = {}

        self.display = dashy.display
        self.session = await dashy.get_service(aiohttp.ClientSession)
        self.browser = await dashy.get_service(Browser)

    async def stop(self) -> None:
        pass

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

                async with aiofiles.open(self.credential_path, "w") as f:
                    await f.write(json.dumps(self.credentials))

        return cast(str, self.credentials["access_token"])

    async def request(
        self,
        method: str,
        path: str,
    ) -> Optional[dict[str, Any]]:
        url = f"https://api.spotify.com{path}"
        token = await self.get_token()
        if not token:
            logger.error("No access token, aborting.")
            return None

        async with await self.session.request(
            method,
            url,
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {token}",
            },
            raise_for_status=True,
        ) as r:
            if r.status == 204:
                return None
            return cast(dict[str, Any], await r.json())

    async def next(self, *, force: bool) -> Union[Literal["SKIP"], None, Image.Image]:
        if not self.credentials.get("access_token"):
            return "SKIP"

        np = await self.request(
            "GET", "/v1/me/player/currently-playing?additional_types=track,episode"
        )
        if (
            np is not None
            and np["is_playing"]
            and np["currently_playing_type"] in ("track", "episode")
        ):
            if force or np["item"]["id"] != self.last_id:
                image = await self.render_item(np["item"])
                self.last_id = np["item"]["id"]
                return image
            return None

        self.last_id = None
        return "SKIP"

    async def render_item(
        self,
        item: dict[str, Any],
    ) -> Image:
        async def handle_cover(route: Route) -> None:
            if item["type"] == "episode":
                image_set = item["images"]
            else:
                image_set = item["album"]["images"]

            if not image_set:
                await route.fulfill(status=404)
                return

            async with self.session.get(image_set[0]["url"]) as r:
                status = r.status
                data = await r.read()
                content_type = r.headers.get("content-type")

            await route.fulfill(status=status, body=data, content_type=content_type)

        if item["type"] == "episode":
            artist = item["show"]["name"]
        else:
            artist = ", ".join(artist["name"] for artist in item["artists"])

        soup = BeautifulSoup(self.template, "html.parser")
        soup.find(id="title").append(item["name"])
        soup.find(id="artist").append(artist)

        width, height = self.display.resolution
        page = await self.browser.new_page(viewport={"width": width, "height": height})
        try:
            await page.route("http://localhost/cover.png", handle_cover)
            await page.set_content(str(soup), wait_until="networkidle")
            image_data = await page.screenshot()
            return Image.open(BytesIO(image_data))
        finally:
            await page.close()
