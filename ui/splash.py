from PIL import Image, ImageFont
from luma.core.render import canvas
from time import sleep
from pathlib import Path
import ui.config as config

SPLASHES_DIR = Path.home() / "keycrow" / "splashes"
font_big   = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11)

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

def show_default(device, ok_button):
    blink = True
    while True:
        with canvas(device) as draw:
            draw.rectangle(device.bounding_box, outline="black", fill="black")
            draw.text((18, 12), "KeyCrow", font=font_big, fill="white")
            draw.text((28, 36), "v0.1", font=font_small, fill="white")
            if blink:
                draw.text((28, 50), "Press OK", font=font_small, fill="white")
        blink = not blink
        if ok_button.is_pressed:
            sleep(0.2)
            return
        sleep(0.4)

def show(device, ok_button):
    name = config.get_splash()

    if name == "default":
        show_default(device, ok_button)
        return

    frames = get_frames(name)
    if not frames:
        show_default(device, ok_button)
        return

    while True:
        for frame in frames:
            device.display(frame)
            sleep(0.03)
            if ok_button.is_pressed:
                sleep(0.2)
                return
