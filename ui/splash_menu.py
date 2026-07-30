from luma.core.render import canvas
from PIL import ImageFont
from pathlib import Path
from time import time
import ui.config as config
import ui.status as status

font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 12)
font_item  = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11)

LIST_TOP = 16
ITEM_HEIGHT = 15
SPLASHES_DIR = Path.home() / "keycrow" / "splashes"

_scroll_pos = 0.0
_scroll_dir = 1
_last_time = time()

def get_available_splashes():
    splashes = ["default"]
    if SPLASHES_DIR.exists():
        for d in sorted(SPLASHES_DIR.iterdir()):
            if d.is_dir():
                splashes.append(d.name)
    return splashes

def get_items():
    return ["Current", "Edit", "Back"]

def get_edit_items():
    items = get_available_splashes()
    items.append("Back")
    return items

def _measure(text):
    bbox = font_item.getbbox(text)
    return bbox[2] - bbox[0]

def draw(device, selected, scroll_offset, current_name=None):
    global _scroll_pos, _scroll_dir, _last_time

    if current_name is None:
        current_name = config.get_splash()

    with canvas(device) as draw:
        draw.rectangle(device.bounding_box, outline="black", fill="black")

        # Title
        draw.text((4, 0), "Splash", font=font_title, fill="white")
        draw.line((0, 14, 127, 14), fill="white")
        status.draw_menu_icons(draw, y=2)

        y = LIST_TOP

        # ===== Current line =====
        if selected == 0:
            draw.rectangle((1, y, 126, y + ITEM_HEIGHT - 1), fill="white")
            text_color = "black"
        else:
            text_color = "white"

        # Fixed parts
        prefix = "Current: ("
        suffix = ")"
        
        # Draw fixed prefix
        draw.text((5, y + 2), prefix, font=font_item, fill=text_color)
        prefix_w = _measure(prefix)
        
        # Starting point of the name (right after the fixed '(' )
        name_start_x = 5 + prefix_w + 1
        
        # Hard maximum for the closing )
        max_close_x = 122
        suffix_w = _measure(suffix)
        
        # Available width for the name
        available = max_close_x - name_start_x - suffix_w - 2
        name_w = _measure(current_name)

        if name_w <= available:
            # Short name - no scrolling needed
            draw.text((name_start_x, y + 2), current_name, font=font_item, fill=text_color)
            close_x = name_start_x + name_w + 1
            draw.text((close_x, y + 2), suffix, font=font_item, fill=text_color)
            _scroll_pos = 0
        else:
            # Long name - bounce scroll
            now = time()
            dt = now - _last_time
            _last_time = now

            speed = 30  # pixels per second
            _scroll_pos += _scroll_dir * speed * dt

            max_scroll = name_w - available
            if _scroll_pos >= max_scroll:
                _scroll_pos = max_scroll
                _scroll_dir = -1
            elif _scroll_pos <= 0:
                _scroll_pos = 0
                _scroll_dir = 1

            # Draw the scrolling name by clipping
            # We use a simple character window for reliability
            char_w = 6
            max_chars = max(4, int(available / char_w))
            start_char = int(_scroll_pos / char_w)
            visible = current_name[start_char:start_char + max_chars]

            draw.text((name_start_x, y + 2), visible, font=font_item, fill=text_color)
            
            # ) locked at maximum position
            draw.text((max_close_x - suffix_w, y + 2), suffix, font=font_item, fill=text_color)

        # ===== Edit =====
        y = LIST_TOP + ITEM_HEIGHT
        if selected == 1:
            draw.rectangle((1, y, 126, y + ITEM_HEIGHT - 1), fill="white")
            draw.text((5, y + 2), "Edit", font=font_item, fill="black")
        else:
            draw.text((5, y + 2), "Edit", font=font_item, fill="white")

        # ===== Back =====
        y = LIST_TOP + ITEM_HEIGHT * 2
        if selected == 2:
            draw.rectangle((1, y, 126, y + ITEM_HEIGHT - 1), fill="white")
            draw.text((5, y + 2), "Back", font=font_item, fill="black")
        else:
            draw.text((5, y + 2), "Back", font=font_item, fill="white")

    return 0

def draw_edit_pick(device, selected, scroll_offset):
    items = get_edit_items()
    current = config.get_splash()

    if selected < scroll_offset:
        scroll_offset = selected
    elif selected >= scroll_offset + 3:
        scroll_offset = selected - 2

    with canvas(device) as draw:
        draw.rectangle(device.bounding_box, outline="black", fill="black")
        draw.text((4, 0), "Edit Splash", font=font_title, fill="white")
        draw.line((0, 14, 127, 14), fill="white")
        status.draw_menu_icons(draw, y=2)

        visible = items[scroll_offset:scroll_offset + 3]
        for row, item in enumerate(visible):
            i = scroll_offset + row
            y = LIST_TOP + (row * ITEM_HEIGHT)
            label = f"> {item}" if item == current else item
            if i == selected:
                draw.rectangle((1, y, 126, y + ITEM_HEIGHT - 1), fill="white")
                draw.text((5, y + 2), label, font=font_item, fill="black")
            else:
                draw.text((5, y + 2), label, font=font_item, fill="white")

    return scroll_offset
