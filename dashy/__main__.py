import asyncio

from dotenv import load_dotenv

from dashy.dashboards.spotify_dashboard import spotify_dashboard
from dashy.displays import Display
from dashy.displays.inky_auto import InkyAuto


async def main(display: Display) -> None:
    async for image in spotify_dashboard(display):
        await display.show_image(image)


if __name__ == "__main__":
    load_dotenv()
    display = InkyAuto()
    asyncio.run(main(display))
