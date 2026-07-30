from luma.core.render import canvas
from PIL import ImageFont
from time import time
import ui.config as config
import ui.status as status

font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 12)
font_item  = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11)

LIST_TOP = 16
ITEM_HEIGHT = 15

# Scrolling state
_scroll_pos = 0.0
_scroll_dir = 1
_last_time = time()
_current_scroll_key = None

def _cfg():
    return config.load().get("status", {})

def _set(key, value):
    cfg = config.load()
    if "status" not in cfg:
        cfg["status"] = {}
    cfg["status"][key] = value
    config.save(cfg)

def _onoff(value):
    return "On" if value else "Off"

def _measure(text):
    bbox = font_item.getbbox(text)
    return bbox[2] - bbox[0]

def get_main_items():
    return ["Splash", "Menus", "Back"]

def get_splash_items():
    s = _cfg()
    return [
        f"Battery      {_onoff(s.get('splash_battery', True))}",
        f"Show %       {_onoff(s.get('splash_show_percent', True))}",
        f"Charging     {_onoff(s.get('splash_charging', True))}",
        f"WiFi         {_onoff(s.get('splash_wifi', True))}",
        f"Bluetooth    {_onoff(s.get('splash_bluetooth', True))}",
        f"Background   {s.get('splash_background', 'black').capitalize()}",
        "Position",
        "Icon Order",
        "Back"
    ]

def get_menu_items():
    s = _cfg()
    return [
        f"Battery      {_onoff(s.get('menu_battery', True))}",
        f"Show %       {_onoff(s.get('menu_show_percent', True))}",
        f"Charging     {_onoff(s.get('menu_charging', True))}",
        f"WiFi         {_onoff(s.get('menu_wifi', True))}",
        f"Bluetooth    {_onoff(s.get('menu_bluetooth', True))}",
        f"Background   {s.get('menu_background', 'black').capitalize()}",
        "Back"
    ]

def _draw_value_in_parens(draw, y, label, value, selected, text_color):
    """Draw a line like: Position: ( Top Left ) with fixed ( and stronger scrolling"""
    global _scroll_pos, _scroll_dir, _last_time, _current_scroll_key

    prefix = f"{label}: ("
    suffix = ")"

    if selected:
        draw.rectangle((1, y, 126, y + ITEM_HEIGHT - 1), fill="white")

    # Draw fixed prefix
    draw.text((5, y + 2), prefix, font=font_item, fill=text_color)
    prefix_w = _measure(prefix)

    name_start_x = 5 + prefix_w + 1
    max_close_x = 122
    suffix_w = _measure(suffix)
    available = max_close_x - name_start_x - suffix_w - 2
    value_w = _measure(value)

    # Reset scroll when the value changes
    scroll_key = f"{label}:{value}"
    if scroll_key != _current_scroll_key:
        _current_scroll_key = scroll_key
        _scroll_pos = 0.0
        _scroll_dir = 1
        _last_time = time()

    if value_w <= available:
        # Fits completely
        draw.text((name_start_x, y + 2), value, font=font_item, fill=text_color)
        close_x = name_start_x + value_w + 1
        draw.text((close_x, y + 2), suffix, font=font_item, fill=text_color)
        _scroll_pos = 0
    else:
        # Stronger bounce scroll
        now = time()
        dt = now - _last_time
        _last_time = now

        speed = 45
        _scroll_pos += _scroll_dir * speed * dt

        max_scroll = value_w - available + 4
        if _scroll_pos >= max_scroll:
            _scroll_pos = max_scroll
            _scroll_dir = -1
        elif _scroll_pos <= 0:
            _scroll_pos = 0
            _scroll_dir = 1

        char_w = 5.5
        max_chars = max(5, int(available / char_w))
        start_char = int(_scroll_pos / char_w)
        visible = value[start_char:start_char + max_chars]

        draw.text((name_start_x, y + 2), visible, font=font_item, fill=text_color)
        # ) stays locked at the right
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

    s = _cfg()

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

            if mode == "splash" and item == "Position":
                value = s.get("splash_position", "top_left").replace("_", " ").title()
                _draw_value_in_parens(draw, y, "Position", value, i == selected, text_color)
            elif mode == "splash" and item == "Icon Order":
                value = s.get("splash_order", "battery_wifi_bt")
                _draw_value_in_parens(draw, y, "Order", value, i == selected, text_color)
            else:
                if i == selected:
                    draw.rectangle((1, y, 126, y + ITEM_HEIGHT - 1), fill="white")
                draw.text((5, y + 2), item, font=font_item, fill=text_color)

    return scroll_offset

def toggle(mode, selected):
    if mode == "splash":
        keys = [
            "splash_battery",
            "splash_show_percent",
            "splash_charging",
            "splash_wifi",
            "splash_bluetooth",
            "splash_background",
            "splash_position",
            "splash_order"
        ]
        if selected >= len(keys):
            return

        key = keys[selected]
        s = _cfg()

        if key in ["splash_battery", "splash_show_percent", "splash_charging", "splash_wifi", "splash_bluetooth"]:
            _set(key, not s.get(key, True))

        elif key == "splash_background":
            options = ["black", "white", "none"]
            current = s.get(key, "black")
            idx = options.index(current) if current in options else 0
            _set(key, options[(idx + 1) % len(options)])

        elif key == "splash_position":
            options = [
                "top_left", "top_center", "top_right",
                "middle_left", "middle_center", "middle_right",
                "bottom_left", "bottom_center", "bottom_right"
            ]
            current = s.get(key, "top_left")
            idx = options.index(current) if current in options else 0
            _set(key, options[(idx + 1) % len(options)])

        elif key == "splash_order":
            options = [
                "battery_wifi_bt",
                "bt_wifi_battery",
                "wifi_battery_bt",
                "battery_bt_wifi"
            ]
            current = s.get(key, "battery_wifi_bt")
            idx = options.index(current) if current in options else 0
            _set(key, options[(idx + 1) % len(options)])

    elif mode == "menus":
        keys = [
            "menu_battery",
            "menu_show_percent",
            "menu_charging",
            "menu_wifi",
            "menu_bluetooth",
            "menu_background"
        ]
        if selected >= len(keys):
            return

        key = keys[selected]
        s = _cfg()

        if key in ["menu_battery", "menu_show_percent", "menu_charging", "menu_wifi", "menu_bluetooth"]:
            _set(key, not s.get(key, True))

        elif key == "menu_background":
            options = ["black", "white", "none"]
            current = s.get(key, "black")
            idx = options.index(current) if current in options else 0
            _set(key, options[(idx + 1) % len(options)])
