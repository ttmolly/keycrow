from PIL import ImageFont
import subprocess
import ui.config as config

# ===== Icons =====
WIFI_ICON = [
    "00100100",
    "01011010",
    "10011001",
    "00100100",
    "00100100",
    "00011000",
    "00011000",
    "00000000",
]

BT_ICON = [
    "00011000",
    "00010100",
    "00011000",
    "00100100",
    "01000010",
    "00100100",
    "00011000",
    "00010100",
]

CHARGE_ICON = [
    "00001000",
    "00011000",
    "00111100",
    "01111110",
    "00011100",
    "00011000",
    "00110000",
    "00100000",
]

font_tiny = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 9)

def _draw_icon(draw, x, y, pattern, fill="white"):
    for row, line in enumerate(pattern):
        for col, pixel in enumerate(line):
            if pixel == "1":
                draw.point((x + col, y + row), fill=fill)

def _draw_battery(draw, x, y, percent, fill="white"):
    draw.rectangle((x, y+1, x+11, y+7), outline=fill)
    draw.rectangle((x+12, y+3, x+13, y+5), fill=fill)
    level = max(0, min(9, int(percent / 11)))
    if level > 0:
        draw.rectangle((x+1, y+2, x+1+level, y+6), fill=fill)

def _pisugar_get(command):
    try:
        result = subprocess.check_output(
            ["nc", "-q", "0", "127.0.0.1", "8423"],
            input=f"{command}\n".encode(),
            stderr=subprocess.DEVNULL
        ).decode().strip()
        if ":" in result:
            return result.split(":", 1)[1].strip().lower()
        return result.lower()
    except Exception:
        return None

def get_battery_percent():
    val = _pisugar_get("get battery")
    if val is None:
        return None
    try:
        return int(round(float(val)))
    except:
        return None

def is_charging():
    return _pisugar_get("get battery_charging") == "true"

def is_wifi_connected():
    try:
        result = subprocess.check_output(
            ["nmcli", "-t", "-f", "DEVICE,STATE", "dev"],
            stderr=subprocess.DEVNULL
        ).decode()
        return any(":connected" in line for line in result.strip().split("\n"))
    except Exception:
        return False

def is_bluetooth_on():
    try:
        result = subprocess.check_output(
            ["bluetoothctl", "show"],
            stderr=subprocess.DEVNULL
        ).decode()
        return "Powered: yes" in result
    except Exception:
        return False

def get_status():
    cfg = config.load().get("status", {})
    return {
        "wifi": is_wifi_connected(),
        "bluetooth": is_bluetooth_on(),
        "battery": get_battery_percent(),
        "charging": is_charging(),
        "show_wifi": cfg.get("menu_wifi", True),
        "show_bluetooth": cfg.get("menu_bluetooth", True),
        "show_battery": cfg.get("menu_battery", True),
        "show_percent": cfg.get("menu_show_percent", True),
        "show_charging": cfg.get("menu_charging", True),
        "background": cfg.get("menu_background", "black"),
    }

def draw_menu_icons(draw, y=1):
    st = get_status()
    bg = st.get("background", "black")

    if bg == "white":
        fill = "black"
        box_fill = "white"
    else:
        fill = "white"
        box_fill = "black"

    elements = []

    if st["show_bluetooth"] and st["bluetooth"]:
        elements.append(("bt", 10))

    if st["show_wifi"] and st["wifi"]:
        elements.append(("wifi", 10))

    if st["show_battery"] and st["battery"] is not None:
        w = 15
        if st["show_percent"]:
            w += 16
        if st["show_charging"] and st["charging"]:
            w += 9
        elements.append(("battery", w))

    if not elements:
        return

    total_w = sum(w for _, w in elements) + 3
    x = 126 - total_w

    # Stronger background box for testing
    if bg != "none":
        draw.rectangle((x - 3, 0, 127, 11), fill=box_fill)
        draw.rectangle((x - 3, 0, 127, 11), outline=fill)

    for kind, width in reversed(elements):
        if kind == "bt":
            _draw_icon(draw, x, y, BT_ICON, fill=fill)
        elif kind == "wifi":
            _draw_icon(draw, x, y, WIFI_ICON, fill=fill)
        elif kind == "battery":
            _draw_battery(draw, x, y, st["battery"], fill=fill)
            cx = x + 15
            if st["show_percent"]:
                draw.text((cx, 0), f"{st['battery']}", font=font_tiny, fill=fill)
                cx += 14
            if st["show_charging"] and st["charging"]:
                _draw_icon(draw, cx, y, CHARGE_ICON, fill=fill)
        x += width
