from luma.core.render import canvas
from PIL import ImageFont
import ui.status as status

font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 12)
font_item  = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11)


def draw(device, title, message, sub=""):
    with canvas(device) as draw:
        draw.rectangle(device.bounding_box, outline="black", fill="black")

        draw.text((4, 0), title, font=font_title, fill="white")
        draw.line((0, 14, 127, 14), fill="white")
        status.draw_menu_icons(draw, y=2)

        draw.text((5, 28), message, font=font_item, fill="white")
        if sub:
            draw.text((5, 44), sub, font=font_item, fill="white")

    return None
