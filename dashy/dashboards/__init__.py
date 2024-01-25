import abc
from typing import Literal, Union

from PIL import Image

from dashy.displays import Display


class Dashboard(abc.ABC):
    @abc.abstractmethod
    async def start(self, display: Display) -> None:
        ...

    @abc.abstractmethod
    async def stop(self) -> None:
        ...

    @property
    @abc.abstractmethod
    def min_interval(self) -> float:
        ...

    @abc.abstractmethod
    async def next(self, *, force: bool) -> Union[Literal["SKIP"], None, Image.Image]:
        ...
