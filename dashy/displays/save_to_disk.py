from PIL import Image

from dashy.displays import Display


class SaveToDisk(Display):
    resolution = (800, 480)

    async def show_image(self, image: Image) -> None:
        image.save("screenshot.png", "PNG")
