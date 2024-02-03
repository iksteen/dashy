import abc
from typing import Literal, Optional, Union

from PIL import Image

from dashy.dashy import Dashy


class Dashboard(abc.ABC):
    @abc.abstractmethod
    async def start(self, dashy: Dashy) -> None:
        ...

    @abc.abstractmethod
    async def stop(self) -> None:
        ...

    @property
    @abc.abstractmethod
    def min_interval(self) -> Optional[int]:
        ...

    @abc.abstractmethod
    async def next(self, *, force: bool) -> Union[Literal["SKIP"], None, Image.Image]:
        ...
