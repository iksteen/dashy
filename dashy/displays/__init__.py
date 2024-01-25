import abc
from typing import Tuple

from PIL import Image


class Display(abc.ABC):
    @property
    @abc.abstractmethod
    def resolution(self) -> Tuple[int, int]:
        ...

    @abc.abstractmethod
    async def show_image(self, image: Image) -> None:
        ...
