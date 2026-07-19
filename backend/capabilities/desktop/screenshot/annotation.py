"""Screen annotation utilities using Pillow."""

from __future__ import annotations

# pyrefly: ignore [missing-import]
from PIL import Image, ImageDraw, ImageFilter


class Annotation:
    """Performs image drawing, highlighting, text overlay, and blurring operations."""

    @staticmethod
    def draw_rectangle(
        image: Image.Image,
        box: tuple[int, int, int, int],
        color: str = "red",
        width: int = 3,
    ) -> Image.Image:
        """Draws an outlined bounding box rectangle on the image.

        Args:
            image: Source image.
            box: Bounding coordinates (x0, y0, x1, y1).
            color: Color name or hex value.
            width: Border stroke width in pixels.

        Returns:
            The annotated copy of the image.
        """

        img = image.copy()
        draw = ImageDraw.Draw(img)
        draw.rectangle(box, outline=color, width=width)
        return img

    @staticmethod
    def highlight_region(
        image: Image.Image,
        box: tuple[int, int, int, int],
        color: tuple[int, int, int] | str = "yellow",
        alpha: int = 128,
    ) -> Image.Image:
        """Draws a semi-transparent highlight overlay on the image region.

        Args:
            image: Source image.
            box: Bounding coordinates (x0, y0, x1, y1).
            color: RGB color tuple or color name string.
            alpha: Transparency opacity (0 to 255).

        Returns:
            The annotated copy of the image.
        """

        img = image.copy().convert("RGBA")
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        fill_color = (255, 255, 0, alpha)
        if isinstance(color, str) and color.lower() == "yellow":
            fill_color = (255, 255, 0, alpha)
        elif isinstance(color, str) and color.lower() == "red":
            fill_color = (255, 0, 0, alpha)
        elif isinstance(color, str) and color.lower() == "green":
            fill_color = (0, 255, 0, alpha)
        elif isinstance(color, tuple) and len(color) == 3:
            fill_color = (color[0], color[1], color[2], alpha)

        draw.rectangle(box, fill=fill_color)
        combined = Image.alpha_composite(img, overlay)
        return combined.convert("RGB")

    @staticmethod
    def add_text(
        image: Image.Image,
        text: str,
        position: tuple[int, int],
        color: str = "red",
    ) -> Image.Image:
        """Overlays text onto the image canvas.

        Args:
            image: Source image.
            text: Message string to draw.
            position: Bounding coordinates (x, y).
            color: Text fill color.

        Returns:
            The annotated copy of the image.
        """

        img = image.copy()
        draw = ImageDraw.Draw(img)
        draw.text(position, text, fill=color)
        return img

    @staticmethod
    def blur_region(
        image: Image.Image,
        box: tuple[int, int, int, int],
        radius: int = 10,
    ) -> Image.Image:
        """Blurs the specified region using a Gaussian filter.

        Args:
            image: Source image.
            box: Bounding coordinates (x0, y0, x1, y1).
            radius: Blur strength factor.

        Returns:
            The annotated copy of the image.
        """

        img = image.copy()
        crop = img.crop(box)
        blurred = crop.filter(ImageFilter.GaussianBlur(radius))
        img.paste(blurred, box)
        return img
