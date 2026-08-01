from PIL import Image, ImageFont, ImageDraw
from luma.core.render import canvas
from time import sleep
from pathlib import Path
import core.config as config
import ui.status as status

SPLASHES_DIR = Path.home() / "keycrow" / "splashes"
font_big   = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11)
font_tiny  = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 9)

def get_frames(name):
    folder = SPLASHES_DIR / name
    if not folder.exists():
        return []
    frame_files = sorted([f for f in folder.iterdir() if f.suffix.lower() == ".png"])
    frames = []
    for f in frame_files:
        try:
            frames.append(Image.open(f).convert("1"))
        except:
            pass
    return frames

def _get_position_coords(position, bar_width, bar_height=11):
    """Return (x, y) for the status bar based on position name"""
    positions = {
        "top_left":      (0, 0),
        "top_center":    ((128 - bar_width) // 2, 0),
        "top_right":     (128 - bar_width, 0),
        "middle_left":   (0, (64 - bar_height) // 2),
        "middle_center": ((128 - bar_width) // 2, (64 - bar_height) // 2),
        "middle_right":  (128 - bar_width, (64 - bar_height) // 2),
        "bottom_left":   (0, 64 - bar_height),
        "bottom_center": ((128 - bar_width) // 2, 64 - bar_height),
        "bottom_right":  (128 - bar_width, 64 - bar_height),
    }
    return positions.get(position, (0, 0))

def draw_status_bar(draw):
    """Full featured status bar for the Splash screen"""
    cfg = config.load().get("status", {})
    st = status.get_status()

    # Colors
    bg = cfg.get("splash_background", "black")
    if bg == "white":
        fill = "black"
        box_fill = "white"
    else:
        fill = "white"
        box_fill = "black"

    # Which icons to show + order
    order = cfg.get("splash_order", "battery_wifi_bt")
    order_map = {
        "battery_wifi_bt": ["battery", "wifi", "bt"],
        "bt_wifi_battery": ["bt", "wifi", "battery"],
        "wifi_battery_bt": ["wifi", "battery", "bt"],
        "battery_bt_wifi": ["battery", "bt", "wifi"],
    }
    icon_order = order_map.get(order, ["battery", "wifi", "bt"])

    # Build visible elements
    elements = []
    for kind in icon_order:
        if kind == "battery" and cfg.get("splash_battery", True) and st["battery"] is not None:
            w = 15
            if cfg.get("splash_show_percent", True):
                w += 16
            if cfg.get("splash_charging", True) and st.get("charging"):
                w += 9
            elements.append(("battery", w))
        elif kind == "wifi" and cfg.get("splash_wifi", True) and st["wifi"]:
            elements.append(("wifi", 10))
        elif kind == "bt" and cfg.get("splash_bluetooth", True) and st["bluetooth"]:
            elements.append(("bt", 10))

    if not elements:
        return

    total_w = sum(w for _, w in elements) + 6
    position = cfg.get("splash_position", "top_left")
    bar_x, bar_y = _get_position_coords(position, total_w)

    # Background box
    if bg != "none":
        draw.rectangle((bar_x, bar_y, bar_x + total_w, bar_y + 10), fill=box_fill)
        draw.rectangle((bar_x, bar_y, bar_x + total_w, bar_y + 10), outline=fill)

    # Draw icons
    x = bar_x + 3
    y = bar_y + 1

    for kind, width in elements:
        if kind == "battery":
            status._draw_battery(draw, x, y, st["battery"], fill=fill)
            cx = x + 15
            if cfg.get("splash_show_percent", True):
                draw.text((cx, bar_y), f"{st['battery']}", font=font_tiny, fill=fill)
                cx += 14
            if cfg.get("splash_charging", True) and st.get("charging"):
                status._draw_icon(draw, cx, y, status.CHARGE_ICON, fill=fill)
        elif kind == "wifi":
            status._draw_icon(draw, x, y, status.WIFI_ICON, fill=fill)
        elif kind == "bt":
            status._draw_icon(draw, x, y, status.BT_ICON, fill=fill)
        x += width

def show_default(device, ok_button):
    blink = True
    while True:
        with canvas(device) as draw:
            draw.rectangle(device.bounding_box, outline="black", fill="black")
            draw_status_bar(draw)
            draw.text((18, 18), "KeyCrow", font=font_big, fill="white")
            draw.text((28, 42), "v0.1", font=font_small, fill="white")
            if blink:
                draw.text((28, 54), "Press OK", font=font_small, fill="white")
        blink = not blink
        if ok_button.is_pressed:
            sleep(0.2)
            return
        sleep(0.4)

def show_custom(device, ok_button, name):
    frames = get_frames(name)
    if not frames:
        show_default(device, ok_button)
        return

    while True:
        for frame in frames:
            img = frame.convert("RGB")
            d = ImageDraw.Draw(img)
            draw_status_bar(d)
            final = img.convert("1")
            device.display(final)
            sleep(0.03)
            if ok_button.is_pressed:
                sleep(0.2)
                return

def show(device, ok_button):
    name = config.get_splash()
    if name == "default":
        show_default(device, ok_button)
    else:
        show_custom(device, ok_button, name)
