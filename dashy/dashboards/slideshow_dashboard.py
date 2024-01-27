import math
import random
import time
from pathlib import Path
from typing import Literal, Union

from PIL import Image

from dashy.dashboards import Dashboard
from dashy.displays import Display

DEFAULT_INTERVAL = 3600.0
DEFAULT_PATH = Path.home() / "Pictures"


class SlideshowDashboard(Dashboard):
    display: Display

    last_update = None

    def __init__(
        self,
        *,
        path: Union[Path, str] = DEFAULT_PATH,
        interval: float = DEFAULT_INTERVAL,
        mode: Literal["FIT", "COVER"] = "FIT",
    ) -> None:
        if isinstance(path, str):
            path = Path(path).expanduser()
        self.interval = interval
        self.mode = mode

        self.file_list = []

        for file in path.iterdir():
            if file.is_file():
                try:
                    im = Image.open(file)
                    im.verify()
                    im.close()
                except Exception:
                    continue
                self.file_list.append(file)
        random.shuffle(self.file_list)

    async def start(self, display: Display) -> None:
        self.display = display

    async def stop(self) -> None:
        pass

    @property
    def min_interval(self) -> float:
        if len(self.file_list) < 2:
            return math.inf

        if self.last_update is None:
            return self.interval

        return max(0.0, self.interval - (time.time() - self.last_update))

    async def next(self, *, force: bool) -> Union[Literal["SKIP"], None, Image.Image]:
        if not self.file_list:
            return "SKIP"

        if force or self.min_interval == 0.0:
            image_path = self.file_list.pop(0)
            self.file_list.append(image_path)
            self.last_update = time.time()

            canvas = Image.new("RGBA", self.display.resolution)

            im = Image.open(image_path)

            if self.mode == "FIT":
                rescale_ratio = (
                    canvas.width / im.width
                    if im.width / im.height >= canvas.width / canvas.height
                    else canvas.height / im.height
                )
            else:
                rescale_ratio = (
                    canvas.height / im.height
                    if im.width / im.height >= canvas.width / canvas.height
                    else canvas.width / im.width
                )

            new_width = int(im.width * rescale_ratio)
            new_height = int(im.height * rescale_ratio)

            new_im = im.resize((new_width, new_height))

            x_offset = int((canvas.width - new_width) / 2)
            y_offset = int((canvas.height - new_height) / 2)

            canvas.paste(new_im, (x_offset, y_offset))

            new_im.close()
            im.close()
            return canvas

        return None
