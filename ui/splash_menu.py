from luma.core.render import canvas
from PIL import ImageFont
from pathlib import Path
import ui.config as config

font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 12)
font_item  = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11)

LIST_TOP = 16
ITEM_HEIGHT = 15
VISIBLE_ITEMS = 3
SPLASHES_DIR = Path.home() / "keycrow" / "splashes"

def get_available_splashes():
    splashes = ["default"]
    if SPLASHES_DIR.exists():
        for d in sorted(SPLASHES_DIR.iterdir()):
            if d.is_dir():
                splashes.append(d.name)
    return splashes

def get_items():
    items = get_available_splashes()
    items.append("Edit Splash")
    items.append("Back")
    return items

def get_edit_items():
    items = get_available_splashes()
    items.append("Back")
    return items

def draw(device, selected, scroll_offset):
    items = get_items()
    current = config.get_splash()
    _render(device, items, selected, scroll_offset, f"Splash: {current}", current)
    return _clamp_scroll(selected, scroll_offset)

def draw_edit_pick(device, selected, scroll_offset):
    items = get_edit_items()
    _render(device, items, selected, scroll_offset, "Edit Splash", None)
    return _clamp_scroll(selected, scroll_offset)

def _clamp_scroll(selected, scroll_offset):
    if selected < scroll_offset:
        return selected
    elif selected >= scroll_offset + VISIBLE_ITEMS:
        return selected - VISIBLE_ITEMS + 1
    return scroll_offset

def _render(device, items, selected, scroll_offset, title, marked):
    scroll_offset = _clamp_scroll(selected, scroll_offset)

    with canvas(device) as draw:
        draw.rectangle(device.bounding_box, outline="black", fill="black")
        draw.text((4, 0), title, font=font_title, fill="white")
        draw.line((0, 14, 127, 14), fill="white")

        visible = items[scroll_offset:scroll_offset + VISIBLE_ITEMS]
        for row, item in enumerate(visible):
            i = scroll_offset + row
            y = LIST_TOP + (row * ITEM_HEIGHT)
            label = f"> {item}" if item == marked else item
            if i == selected:
                draw.rectangle((1, y, 126, y + ITEM_HEIGHT - 1), fill="white")
                draw.text((5, y + 2), label, font=font_item, fill="black")
            else:
                draw.text((5, y + 2), label, font=font_item, fill="white")
