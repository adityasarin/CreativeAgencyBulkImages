import io
import re

from PIL import Image, ImageFilter


class AdCompositor:
    """Composites a cleaned product PNG onto a generated ad image."""

    def composite(
        self,
        ad_image_bytes: bytes,
        product_png_bytes: bytes,
        placement_zone: str = "",
        product_scale: float = 0.38,
    ) -> bytes:
        ad = Image.open(io.BytesIO(ad_image_bytes)).convert("RGBA")
        product = Image.open(io.BytesIO(product_png_bytes)).convert("RGBA")

        ad_w, ad_h = ad.size

        # Scale product to product_scale fraction of ad width
        new_w = int(ad_w * product_scale)
        ratio = new_w / product.width
        new_h = int(product.height * ratio)
        product = product.resize((new_w, new_h), Image.LANCZOS)

        # Determine vertical placement from zone description or default
        top_pct = self._parse_top_pct(placement_zone)
        top_y = int(ad_h * top_pct)
        # Centre horizontally
        left_x = (ad_w - new_w) // 2

        # Add drop shadow under product
        product_with_shadow = self._add_drop_shadow(product)
        shadow_offset_x = 4
        shadow_offset_y = 6
        shadow_left = left_x - shadow_offset_x
        shadow_top = top_y - shadow_offset_y

        canvas = ad.copy()
        canvas.alpha_composite(product_with_shadow, dest=(shadow_left, shadow_top))

        # Convert back to RGB PNG
        final = canvas.convert("RGB")
        buf = io.BytesIO()
        final.save(buf, format="PNG")
        return buf.getvalue()

    def _parse_top_pct(self, zone: str) -> float:
        """Extract top vertical position from a zone description string."""
        if not zone or zone.upper().startswith("N/A"):
            return 0.22  # default: just below top UI zone
        # Look for first percentage-like number, e.g. "between 20% and 65%"
        numbers = re.findall(r"(\d+)\s*%", zone)
        if numbers:
            return int(numbers[0]) / 100
        return 0.22

    def _add_drop_shadow(
        self,
        product_img: Image.Image,
        offset: tuple[int, int] = (4, 6),
        blur_radius: int = 8,
        opacity: int = 100,  # 0-255
    ) -> Image.Image:
        shadow_color = (0, 0, 0, opacity)
        w, h = product_img.size
        canvas_w = w + abs(offset[0]) + blur_radius * 2
        canvas_h = h + abs(offset[1]) + blur_radius * 2

        shadow = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
        # Place a solid silhouette of the product
        silhouette = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        mask = product_img.split()[3]  # alpha channel
        shadow_layer = Image.new("RGBA", (w, h), shadow_color)
        silhouette.paste(shadow_layer, mask=mask)
        shadow.paste(silhouette, (blur_radius, blur_radius))
        shadow = shadow.filter(ImageFilter.GaussianBlur(radius=blur_radius))

        # Composite product on top of shadow
        canvas = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
        canvas.alpha_composite(shadow)
        prod_x = blur_radius - offset[0]
        prod_y = blur_radius - offset[1]
        canvas.alpha_composite(product_img, dest=(prod_x, prod_y))
        return canvas
