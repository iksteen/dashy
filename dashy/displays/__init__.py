from __future__ import annotations

import abc
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PIL import Image

    from dashy.dashy import Dashy


class Display(abc.ABC):
    async def start(self, dashy: Dashy) -> None:  # noqa: B027
        pass

    async def stop(self) -> None:  # noqa: B027
        pass

    @property
    @abc.abstractmethod
    def resolution(self) -> tuple[int, int]:
        ...

    @abc.abstractmethod
    async def show_image(self, image: Image) -> None:
        ...
