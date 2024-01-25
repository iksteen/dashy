import asyncio
import os
from io import BytesIO
from typing import List

import aiohttp
import spotify
from bs4 import BeautifulSoup
from PIL import Image
from playwright.async_api import Browser, Route
from playwright.async_api import async_playwright as playwright

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


async def render_track(
    display: Display,
    session: aiohttp.ClientSession,
    browser: Browser,
    track: spotify.Track,
    playlist_images: List[spotify.Image],
) -> Image:
    async def handle_cover(route: Route) -> None:
        if route.request.url.endswith("/covers/playlist.png"):
            image_set = playlist_images if playlist_images else track.album.images
        elif route.request.url.endswith("/covers/album.png"):
            image_set = track.album.images
        else:
            image_set = track.images

        if not image_set:
            await route.fulfill(status=404)
            return

        async with session.get(image_set[0].url) as response:
            status = response.status
            data = await response.read()
            content_type = response.headers.get("content-type")

        await route.fulfill(status=status, body=data, content_type=content_type)

    soup = BeautifulSoup(template, "html.parser")
    soup.find(id="title").append(track.name)
    soup.find(id="artist").append(track.artist.name)

    width, height = display.resolution
    page = await browser.new_page(viewport={"width": width, "height": height})
    await page.route("http://localhost/covers/*.png", handle_cover)
    await page.set_content(str(soup), wait_until="networkidle")
    image_data = await page.screenshot()
    await page.close()
    return Image.open(BytesIO(image_data))


async def spotify_dashboard(display: Display) -> None:
    client_id = os.environ.get("SPOTIFY_CLIENT_ID")
    client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")
    access_token = os.environ.get("SPOTIFY_ACCESS_TOKEN")
    refresh_token = os.environ.get("SPOTIFY_REFRESH_TOKEN")

    async with spotify.Client(
        client_id, client_secret
    ) as client, spotify.User.from_token(
        client, access_token, refresh_token
    ) as user, aiohttp.ClientSession() as session, playwright() as p:
        browser = await p.chromium.launch()

        last_track = None
        while True:
            np = await user.currently_playing()
            if np.get("currently_playing_type") == "track":
                if np.get("context") and np["context"].type == "playlist":
                    cover_images = await user.http.get_playlist_cover_image(
                        np["context"].uri.split(":")[-1],
                    )
                    playlist_images = [
                        spotify.models.Image(**image) for image in cover_images
                    ]
                else:
                    playlist_images = []
                item = np["item"]
                if item.id != last_track:
                    image = await render_track(
                        display,
                        session,
                        browser,
                        item,
                        playlist_images,
                    )
                    await display.show_image(image)
                    last_track = item.id

            await asyncio.sleep(1)


if __name__ == "__main__":
    from dotenv import load_dotenv

    from dashy.displays.save_to_disk import SaveToDisk

    load_dotenv()
    display = SaveToDisk()
    asyncio.run(spotify_dashboard(display))
