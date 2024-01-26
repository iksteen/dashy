from __future__ import annotations

import abc
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PIL import Image


class Display(abc.ABC):
    @property
    @abc.abstractmethod
    def resolution(self) -> tuple[int, int]:
        ...

    @abc.abstractmethod
    async def show_image(self, image: Image) -> None:
        ...
