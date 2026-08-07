from luma.core.render import canvas
from PIL import ImageFont
import ui.status as status

font_item = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)
font_tiny = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 9)


def _fmt(seconds):
    if seconds is None or seconds < 0:
        return "--:--"
    s = int(seconds)
    return f"{s // 60}:{s % 60:02d}"


def _draw_play(draw, x, y):
    draw.polygon([(x, y), (x, y + 12), (x + 10, y + 6)], fill="white")


def _draw_pause(draw, x, y):
    draw.rectangle((x, y, x + 3, y + 12), fill="white")
    draw.rectangle((x + 7, y, x + 10, y + 12), fill="white")


def _draw_prev(draw, x, y):
    draw.polygon([(x + 8, y), (x, y + 6), (x + 8, y + 12)], fill="white")
    draw.polygon([(x + 16, y), (x + 8, y + 6), (x + 16, y + 12)], fill="white")


def _draw_next(draw, x, y):
    draw.polygon([(x, y), (x + 8, y + 6), (x, y + 12)], fill="white")
    draw.polygon([(x + 8, y), (x + 16, y + 6), (x + 8, y + 12)], fill="white")


def draw(device, track_name, paused, elapsed=0, duration=0, volume=80, output_mode="aux"):
    with canvas(device) as draw:
        draw.rectangle(device.bounding_box, outline="black", fill="black")

        # Menu splash icons (right side)
        status.draw_menu_icons(draw, y=2)

        # ----- Volume (label left, bar a bit lower) -----
        draw.text((2, 0), "Volume", font=font_tiny, fill="white")
        draw.text((2, 12), "-", font=font_item, fill="white")
        draw.text((100, 12), "+", font=font_item, fill="white")

        bar_x, bar_y, bar_w, bar_h = 12, 14, 84, 5
        draw.rectangle((bar_x, bar_y, bar_x + bar_w, bar_y + bar_h), outline="white")
        fill_w = int((max(0, min(100, volume)) / 100.0) * (bar_w - 2))
        if fill_w > 0:
            draw.rectangle(
                (bar_x + 1, bar_y + 1, bar_x + 1 + fill_w, bar_y + bar_h - 1),
                fill="white",
            )

        # ----- Play / pause + title -----
        if paused:
            _draw_pause(draw, 4, 24)
        else:
            _draw_play(draw, 4, 24)

        name = track_name or "-"
        if name.lower().endswith(".mp3"):
            name = name[:-4]
        if len(name) > 16:
            name = name[:15] + "…"
        draw.text((22, 26), name, font=font_item, fill="white")

        mode_label = {
            "aux": "(AUX)",
            "bluetooth": "(BLE)",
            "auto": "(AUTO)",
        }.get(output_mode, f"({output_mode.upper()})")
        draw.text((48, 38), mode_label, font=font_tiny, fill="white")

        # ----- Prev / time / next -----
        _draw_prev(draw, 2, 46)
        _draw_next(draw, 110, 46)

        time_str = f"{_fmt(elapsed)} / {_fmt(duration if duration else None)}"
        draw.text((36, 48), time_str, font=font_tiny, fill="white")

        # progress bar
        px, py, pw, ph = 24, 58, 80, 4
        draw.rectangle((px, py, px + pw, py + ph), outline="white")
        if duration and duration > 0:
            ratio = max(0.0, min(1.0, float(elapsed) / float(duration)))
            fw = int(ratio * (pw - 2))
            if fw > 0:
                draw.rectangle((px + 1, py + 1, px + 1 + fw, py + ph - 1), fill="white")
            kx = px + int(ratio * pw)
            draw.rectangle((kx - 1, py - 1, kx + 2, py + ph + 1), fill="white")

    return None
