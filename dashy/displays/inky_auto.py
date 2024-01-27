from inky.auto import auto

from dashy.displays.inky_base import InkyBase, InkyDisplay


class InkyAuto(InkyBase):
    def __init__(self, *, saturation: float = 0.75) -> None:
        super().__init__(saturation=saturation)
        self._device: InkyDisplay = auto()

    @property
    def device(self) -> InkyDisplay:
        return self._device
