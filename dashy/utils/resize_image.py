from __future__ import annotations

from typing import Literal

from PIL import Image


def resize_image(
    im: Image.Image, size: tuple[int, int], *, mode: Literal["FIT", "COVER"] = "FIT"
) -> Image.Image:
    canvas = Image.new("RGBA", size)

    if mode == "FIT":
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

    resized_im = im.resize((new_width, new_height))

    x_offset = int((canvas.width - new_width) / 2)
    y_offset = int((canvas.height - new_height) / 2)

    canvas.paste(resized_im, (x_offset, y_offset))

    resized_im.close()

    return canvas
