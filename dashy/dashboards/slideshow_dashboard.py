import random
import time
from pathlib import Path
from typing import Literal, Optional, Union

from PIL import Image

from dashy.dashboards import Dashboard
from dashy.displays import Display
from dashy.utils.resize_image import resize_image

DEFAULT_INTERVAL = 3600
DEFAULT_PATH = Path.home() / "Pictures"


class SlideshowDashboard(Dashboard):
    display: Display

    last_update = None

    def __init__(
        self,
        *,
        path: Union[Path, str] = DEFAULT_PATH,
        interval: int = DEFAULT_INTERVAL,
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
    def min_interval(self) -> Optional[int]:
        if len(self.file_list) < 2:
            return None

        if self.last_update is None:
            return 0

        return max(0, self.interval - int(time.time() - self.last_update))

    async def next(self, *, force: bool) -> Union[Literal["SKIP"], None, Image.Image]:
        if not self.file_list:
            return "SKIP"

        if force or self.min_interval == 0:
            if self.min_interval == 0:
                self.file_list.append(self.file_list.pop(0))
                self.last_update = time.time()

            im = Image.open(self.file_list[0])
            try:
                return resize_image(im, self.display.resolution, mode=self.mode)
            finally:
                im.close()

        return None
