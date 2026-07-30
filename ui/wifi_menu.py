from luma.core.render import canvas
from PIL import ImageFont
import ui.status as status

font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 12)
font_item  = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11)

ITEMS = [
    "Scan Networks",
    "Connect",
    "Monitor Mode",
    "Back"
]

LIST_TOP = 16
ITEM_HEIGHT = 15
VISIBLE_ITEMS = 3

def draw(device, selected, scroll_offset):
    if selected < scroll_offset:
        scroll_offset = selected
    elif selected >= scroll_offset + VISIBLE_ITEMS:
        scroll_offset = selected - VISIBLE_ITEMS + 1

    with canvas(device) as draw:
        draw.rectangle(device.bounding_box, outline="black", fill="black")

        # Title
        draw.text((4, 0), "WiFi Tools", font=font_title, fill="white")
        draw.line((0, 14, 127, 14), fill="white")

        # Status icons
        status.draw_menu_icons(draw, y=2)

        visible = ITEMS[scroll_offset:scroll_offset + VISIBLE_ITEMS]

        for row, item in enumerate(visible):
            i = scroll_offset + row
            y = LIST_TOP + (row * ITEM_HEIGHT)
            if i == selected:
                draw.rectangle((1, y, 126, y + ITEM_HEIGHT - 1), fill="white")
                draw.text((5, y + 2), item, font=font_item, fill="black")
            else:
                draw.text((5, y + 2), item, font=font_item, fill="white")

        if scroll_offset > 0:
            draw.text((119, LIST_TOP), "^", font=font_item, fill="white")
        if scroll_offset + VISIBLE_ITEMS < len(ITEMS):
            draw.text((119, LIST_TOP + (VISIBLE_ITEMS - 1) * ITEM_HEIGHT), "v", font=font_item, fill="white")

    return scroll_offset
