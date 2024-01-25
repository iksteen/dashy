import asyncio
import os
from io import BytesIO
from typing import List, Literal, Union

import aiohttp
import spotify
from bs4 import BeautifulSoup
from PIL import Image
from playwright.async_api import Browser, Playwright, Route
from playwright.async_api import async_playwright as playwright

from dashy.dashboards import Dashboard
from dashy.displays import Display

template = """
<html>
    <head>
        <style type="text/css">
            body {
                width: 100%;
                height: 100%;
                margin: 0px;
                background-image: url("http://localhost/covers/track.png");
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
    display: Display
    spotify: spotify.Client
    spotify_user: spotify.models.User
    session: aiohttp.ClientSession
    playwright: Playwright
    browser: Browser

    min_interval = 1.0

    def __init__(self) -> None:
        self.last_track = None

    async def start(self, display: Display) -> None:
        self.display = display
        client_id = os.environ.get("SPOTIFY_CLIENT_ID")
        client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")
        access_token = os.environ.get("SPOTIFY_ACCESS_TOKEN")
        refresh_token = os.environ.get("SPOTIFY_REFRESH_TOKEN")

        self.spotify = spotify.Client(client_id, client_secret)
        self.spotify_user = await spotify.models.User.from_token(
            self.spotify, access_token, refresh_token
        ).__aenter__()
        self.session = aiohttp.ClientSession()
        self.playwright = await playwright().start()
        self.browser = await self.playwright.chromium.launch()

    async def stop(self) -> None:
        await self.browser.close()
        await self.playwright.stop()
        await self.session.close()
        await self.spotify_user.__aexit__(None, None, None)
        await self.spotify.close()

    async def next(self, *, force: bool) -> Union[Literal["SKIP"], None, Image.Image]:
        np = await self.spotify_user.currently_playing()
        if np.get("is_playing") and np.get("currently_playing_type") == "track":
            item = np["item"]

            if np.get("context") and np["context"].type == "playlist":
                cover_images = await self.spotify_user.http.get_playlist_cover_image(
                    np["context"].uri.split(":")[-1],
                )
                playlist_images = [
                    spotify.models.Image(**image) for image in cover_images
                ]
            else:
                playlist_images = []

            if force or item.id != self.last_track:
                image = await self.render_track(
                    item,
                    playlist_images,
                )
                self.last_track = item.id

                return image
            return None

        self.last_track = None
        return "SKIP"

    async def render_track(
        self,
        track: spotify.models.Track,
        playlist_images: List[spotify.models.Image],
    ) -> Image:
        async def handle_cover(route: Route) -> None:
            if route.request.url == "http://localhost/covers/playlist.png":
                image_set = playlist_images if playlist_images else track.album.images
            elif route.request.url == "http://localhost/covers/album.png":
                image_set = track.album.images
            else:
                image_set = track.images

            if not image_set:
                await route.fulfill(status=404)
                return

            async with self.session.get(image_set[0].url) as response:
                status = response.status
                data = await response.read()
                content_type = response.headers.get("content-type")

            await route.fulfill(status=status, body=data, content_type=content_type)

        soup = BeautifulSoup(template, "html.parser")
        soup.find(id="title").append(track.name)
        soup.find(id="artist").append(track.artist.name)

        width, height = self.display.resolution
        page = await self.browser.new_page(viewport={"width": width, "height": height})
        try:
            await page.route("http://localhost/covers/*.png", handle_cover)
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
