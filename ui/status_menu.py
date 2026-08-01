from luma.core.render import canvas
from PIL import ImageFont
from time import time
import core.config as config
import ui.status as status

font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 12)
font_item  = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11)

LIST_TOP = 16
ITEM_HEIGHT = 15

_scroll_state = {}

_MODES = {
    "splash": {
        "prefix": "splash_",
        "options": {
            "background": ["black", "white", "none"],
            "position": [
                "top_left", "top_center", "top_right",
                "middle_left", "middle_center", "middle_right",
                "bottom_left", "bottom_center", "bottom_right",
            ],
            "order": [
                "battery_wifi_bt", "bt_wifi_battery",
                "wifi_battery_bt", "battery_bt_wifi",
            ],
        },
        "defaults": {"background": "black", "position": "top_left", "order": "battery_wifi_bt"},
    },
    "menus": {
        "prefix": "menu_",
        "options": {
            "background": ["black", "white", "none"],
            "position": ["left", "center", "right"],
            "order": [
                "battery_wifi_bt", "bt_wifi_battery",
                "wifi_battery_bt", "battery_bt_wifi",
            ],
        },
        "defaults": {"background": "black", "position": "right", "order": "battery_wifi_bt"},
    },
}

_TOGGLE_KEYS = ["battery", "show_percent", "charging", "wifi", "bluetooth"]


def _onoff(value):
    return "On" if value else "Off"

def _measure(text):
    bbox = font_item.getbbox(text)
    return bbox[2] - bbox[0]

def get_main_items():
    return ["Splash", "Menus", "Back"]

def _items_for(prefix, s):
    return [
        f"Battery      {_onoff(s.get(prefix + 'battery', True))}",
        f"Show %       {_onoff(s.get(prefix + 'show_percent', True))}",
        f"Charging     {_onoff(s.get(prefix + 'charging', True))}",
        f"WiFi         {_onoff(s.get(prefix + 'wifi', True))}",
        f"Bluetooth    {_onoff(s.get(prefix + 'bluetooth', True))}",
        f"Background   {s.get(prefix + 'background', 'black').capitalize()}",
        "Position",
        "Icon Order",
        "Back",
    ]

def get_splash_items():
    return _items_for("splash_", config.get_status_dict())

def get_menu_items():
    return _items_for("menu_", config.get_status_dict())

def _draw_value_in_parens(draw, y, label, value, selected, text_color):
    state = _scroll_state.setdefault(label, {"pos": 0.0, "dir": 1, "last_time": time(), "key": None})

    prefix = f"{label}: ("
    suffix = ")"

    if selected:
        draw.rectangle((1, y, 126, y + ITEM_HEIGHT - 1), fill="white")

    draw.text((5, y + 2), prefix, font=font_item, fill=text_color)
    prefix_w = _measure(prefix)

    name_start_x = 5 + prefix_w + 1
    max_close_x = 122
    suffix_w = _measure(suffix)
    available = max_close_x - name_start_x - suffix_w - 2

    padded_value = value
    while _measure(padded_value) <= available:
        padded_value += "  "
    value_w = _measure(padded_value)

    scroll_key = f"{label}:{value}"
    if scroll_key != state["key"]:
        state["key"] = scroll_key
        state["pos"] = 0.0
        state["dir"] = 1
        state["last_time"] = time()

    now = time()
    dt = now - state["last_time"]
    state["last_time"] = now

    speed = 30
    state["pos"] += state["dir"] * speed * dt

    max_scroll = value_w - available
    if state["pos"] >= max_scroll:
        state["pos"] = max_scroll
        state["dir"] = -1
    elif state["pos"] <= 0:
        state["pos"] = 0
        state["dir"] = 1

    char_w = 6
    max_chars = max(4, int(available / char_w))
    start_char = int(state["pos"] / char_w)
    visible = padded_value[start_char:start_char + max_chars]

    draw.text((name_start_x, y + 2), visible, font=font_item, fill=text_color)
    draw.text((max_close_x - suffix_w, y + 2), suffix, font=font_item, fill=text_color)

def draw(device, selected, scroll_offset, mode="main"):
    if mode == "main":
        items = get_main_items()
        title = "Status Bar"
    elif mode == "splash":
        items = get_splash_items()
        title = "Splash Icons"
    else:
        items = get_menu_items()
        title = "Menu Icons"

    if selected < scroll_offset:
        scroll_offset = selected
    elif selected >= scroll_offset + 3:
        scroll_offset = selected - 2

    s = config.get_status_dict()
    cfg_mode = _MODES.get(mode)

    with canvas(device) as draw:
        draw.rectangle(device.bounding_box, outline="black", fill="black")
        draw.text((4, 0), title, font=font_title, fill="white")
        draw.line((0, 14, 127, 14), fill="white")
        status.draw_menu_icons(draw, y=2)

        visible = items[scroll_offset:scroll_offset + 3]
        for row, item in enumerate(visible):
            i = scroll_offset + row
            y = LIST_TOP + (row * ITEM_HEIGHT)
            text_color = "black" if i == selected else "white"

            if cfg_mode and item in ("Position", "Icon Order"):
                short_key = "position" if item == "Position" else "order"
                label = "Position" if item == "Position" else "Order"
                default = cfg_mode["defaults"][short_key]
                full_key = cfg_mode["prefix"] + short_key
                raw_value = s.get(full_key, default)
                value = raw_value.replace("_", " ").title()
                _draw_value_in_parens(draw, y, label, value, i == selected, text_color)
            else:
                if i == selected:
                    draw.rectangle((1, y, 126, y + ITEM_HEIGHT - 1), fill="white")
                draw.text((5, y + 2), item, font=font_item, fill=text_color)

    return scroll_offset

def toggle(mode, selected):
    cfg_mode = _MODES.get(mode)
    if cfg_mode is None:
        return

    items = get_splash_items() if mode == "splash" else get_menu_items()
    if selected >= len(items) - 1:
        return

    row_keys = ["battery", "show_percent", "charging", "wifi", "bluetooth", "background", "position", "order"]
    short_key = row_keys[selected]
    full_key = cfg_mode["prefix"] + short_key
    s = config.get_status_dict()

    if short_key in _TOGGLE_KEYS:
        config.set_status(full_key, not s.get(full_key, True))
        return

    options = cfg_mode["options"].get(short_key)
    if options is None:
        return

    default = cfg_mode["defaults"][short_key]
    current = s.get(full_key, default)
    idx = options.index(current) if current in options else 0
    config.set_status(full_key, options[(idx + 1) % len(options)])
