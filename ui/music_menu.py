from luma.core.render import canvas
from PIL import ImageFont
import ui.status as status

font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 12)
font_item  = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11)

LIST_TOP = 16
ITEM_HEIGHT = 15
VISIBLE_ITEMS = 3


def draw(device, labels, selected, scroll_offset, title="Music"):
    if selected < scroll_offset:
        scroll_offset = selected
    elif selected >= scroll_offset + VISIBLE_ITEMS:
        scroll_offset = selected - VISIBLE_ITEMS + 1

    with canvas(device) as draw:
        draw.rectangle(device.bounding_box, outline="black", fill="black")

        draw.text((4, 0), title, font=font_title, fill="white")
        draw.line((0, 14, 127, 14), fill="white")
        status.draw_menu_icons(draw, y=2)

        visible = labels[scroll_offset:scroll_offset + VISIBLE_ITEMS]

        for row, item in enumerate(visible):
            i = scroll_offset + row
            y = LIST_TOP + (row * ITEM_HEIGHT)
            label = item if len(item) <= 18 else item[:17] + "…"

            if i == selected:
                draw.rectangle((1, y, 126, y + ITEM_HEIGHT - 1), fill="white")
                draw.text((5, y + 2), label, font=font_item, fill="black")
            else:
                draw.text((5, y + 2), label, font=font_item, fill="white")

        if scroll_offset > 0:
            draw.text((119, LIST_TOP), "^", font=font_item, fill="white")
        if scroll_offset + VISIBLE_ITEMS < len(labels):
            draw.text((119, LIST_TOP + (VISIBLE_ITEMS - 1) * ITEM_HEIGHT), "v", font=font_item, fill="white")

    return scroll_offset
