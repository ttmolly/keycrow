from PIL import Image, ImageDraw, ImageEnhance, ImageFont
from luma.core.render import canvas
from pathlib import Path
from time import sleep
import json

SPLASHES_DIR = Path.home() / "keycrow" / "splashes"
font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)

PARAMS = ["Brightness", "Contrast", "Speed"]
STEP   = {"Brightness": 10, "Contrast": 10, "Speed": 1}
LIMITS = {"Brightness": (-100, 100), "Contrast": (-100, 100), "Speed": (1, 30)}

SAVE_ITEMS = ["Save as New", "Replace Original", "Cancel"]


def load_meta(name):
    meta_file = SPLASHES_DIR / name / "meta.json"
    if meta_file.exists():
        try:
            data = json.loads(meta_file.read_text())
            return {"Brightness": 0, "Contrast": 0, "Speed": data.get("fps", 10)}
        except Exception:
            pass
    return {"Brightness": 0, "Contrast": 0, "Speed": 10}


def get_raw_frames(name):
    folder = SPLASHES_DIR / name
    if not folder.exists():
        return []
    frame_files = sorted([f for f in folder.iterdir() if f.suffix.lower() == ".png"])
    frames = []
    for f in frame_files:
        try:
            frames.append(Image.open(f).convert("L"))
        except Exception:
            pass
    return frames


def enhance(img, values):
    b_factor = 1.0 + (values["Brightness"] / 100.0)
    c_factor = 1.0 + (values["Contrast"] / 100.0)
    img = ImageEnhance.Brightness(img).enhance(b_factor)
    img = ImageEnhance.Contrast(img).enhance(c_factor)
    return img


def _draw_frame(device, gray_frame, param, value):
    frame = enhance(gray_frame, _current_values).convert("1")
    d = ImageDraw.Draw(frame)
    label = f"{param} {value:+d}" if param != "Speed" else f"{param} {value}fps"
    d.rectangle((0, 0, 74, 10), fill="black")
    d.text((2, 0), label, font=font_small, fill="white")
    device.display(frame)


_current_values = {"Brightness": 0, "Contrast": 0, "Speed": 10}


def _no_frames_message(device):
    with canvas(device) as draw:
        draw.rectangle(device.bounding_box, outline="black", fill="black")
        draw.text((4, 24), "No frames to", font=font_small, fill="white")
        draw.text((4, 36), "edit for this splash", font=font_small, fill="white")
    sleep(1.2)


font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 12)
font_item = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11)


def draw_save(device, selected, scroll_offset):
    """Draw the 'Save as New / Replace Original / Cancel' menu."""
    with canvas(device) as draw:
        draw.rectangle(device.bounding_box, outline="black", fill="black")
        draw.text((4, 0), "Save Edit", font=font_title, fill="white")
        draw.line((0, 14, 127, 14), fill="white")
        for i, item in enumerate(SAVE_ITEMS):
            y = 16 + (i * 15)
            if i == selected:
                draw.rectangle((1, y, 126, y + 14), fill="white")
                draw.text((5, y + 2), item, font=font_item, fill="black")
            else:
                draw.text((5, y + 2), item, font=font_item, fill="white")
    return scroll_offset


def run_edit(device, buttons, name):
    """Blocking, like run_splash(). Returns (values, raw_frames) to save, or None if cancelled."""
    global _current_values
    raw_frames = get_raw_frames(name)
    if not raw_frames:
        _no_frames_message(device)
        return None

    _current_values = load_meta(name)
    param_idx = 0

    while True:
        param = PARAMS[param_idx]
        delay = 1.0 / max(1, _current_values["Speed"])

        for raw in raw_frames:
            _draw_frame(device, raw, param, _current_values[param])
            sleep(delay)
            if buttons.is_pressed("OK"):
                sleep(0.2)
                return _current_values, raw_frames
            if buttons.is_pressed("BACK"):
                sleep(0.2)
                return None

        while True:
            if buttons.is_pressed("UP"):
                param_idx = (param_idx - 1) % len(PARAMS)
                sleep(0.18)
                break
            elif buttons.is_pressed("DOWN"):
                param_idx = (param_idx + 1) % len(PARAMS)
                sleep(0.18)
                break
            elif buttons.is_pressed("LEFT"):
                lo, hi = LIMITS[param]
                _current_values[param] = max(lo, _current_values[param] - STEP[param])
                sleep(0.15)
                break
            elif buttons.is_pressed("RIGHT"):
                lo, hi = LIMITS[param]
                _current_values[param] = min(hi, _current_values[param] + STEP[param])
                sleep(0.15)
                break
            elif buttons.is_pressed("OK"):
                sleep(0.2)
                return _current_values, raw_frames
            elif buttons.is_pressed("BACK"):
                sleep(0.2)
                return None
            sleep(0.04)


def save_edit(name, values, raw_frames, mode):
    if mode == "replace":
        final_name = name
        target = SPLASHES_DIR / name
    else:
        base = f"New-{name}"
        final_name = base
        target = SPLASHES_DIR / final_name
        n = 1
        while target.exists():
            final_name = f"{base}-{n}"
            target = SPLASHES_DIR / final_name
            n += 1
        target.mkdir(parents=True)

    for i, raw in enumerate(raw_frames):
        baked = enhance(raw, values)
        baked.convert("L").save(target / f"frame_{i:03d}.png")

    (target / "meta.json").write_text(json.dumps({"fps": values["Speed"]}))
    return final_name
