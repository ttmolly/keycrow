from luma.core.render import canvas
from PIL import ImageFont
import ui.status as status

font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 12)
font_item  = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11)


def draw(device, track_name, paused):
    with canvas(device) as draw:
        draw.rectangle(device.bounding_box, outline="black", fill="black")

        draw.text((4, 0), "Now Playing", font=font_title, fill="white")
        draw.line((0, 14, 127, 14), fill="white")
        status.draw_menu_icons(draw, y=2)

        name = track_name or "-"
        if name.lower().endswith(".mp3"):
            name = name[:-4]
        if len(name) > 20:
            name = name[:19] + "…"
        draw.text((5, 24), name, font=font_item, fill="white")

        state = "PAUSED" if paused else "PLAYING"
        draw.text((5, 44), state, font=font_item, fill="white")

        draw.text((5, 54), "OK pause  </> skip", font=font_item, fill="white")

    return None
