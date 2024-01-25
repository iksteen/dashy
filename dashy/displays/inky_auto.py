from inky.auto import auto

from dashy.displays.inky_base import InkyBase, InkyDisplay


class InkyAuto(InkyBase):
    def __init__(self) -> None:
        self._device: InkyDisplay = auto()

    @property
    def device(self) -> InkyDisplay:
        return self._device
