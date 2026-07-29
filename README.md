Here’s a clean README you can use:

```bash
nano ~/keycrow/README.md
```

Paste this:

```markdown
# KeyCrow

**KeyCrow** is a DIY multi-tool inspired by the Flipper Zero, built for the Raspberry Pi.

It features a custom interface on a 1.3" OLED display with physical buttons, modular apps, and support for custom animated splash screens.

## Hardware

- Raspberry Pi 3 Model A+
- Adafruit 1.3" 128x64 OLED (SSD1306, I2C)
- 6 buttons (Up, Down, Left, Right, OK, Back)

## Features (Current)

- Animated splash screen system (custom + default)
- Main menu with clean UI
- WiFi Tools (basic network scanning)
- Settings menu (switch splash screens)
- Modular code structure
- Config system using `config.toml`
- Splash Manager for adding/converting custom animations

## Project Structure

```
keycrow/
├── keycrow.py              # Main entry point
├── config.toml             # Settings
├── ui/                     # Interface & menus
│   ├── splash.py
│   ├── main_menu.py
│   ├── wifi_menu.py
│   ├── settings_menu.py
│   └── config.py
├── apps/                   # Tools / functions
│   └── wifi_scan.py
├── splash_sources/         # Original videos/images
├── splashes/               # Converted splash frames
└── splash_manager.py       # Tool to add new splashes
```

## Getting Started

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install luma.oled gpiozero pillow toml
   ```
3. Run:
   ```bash
   python keycrow.py
   ```

## Controls

- **UP / DOWN** → Navigate menus (wrapping enabled)
- **OK** → Select
- **BACK** → Go back / return to splash

## Future Plans

- Better WiFi tools
- Sub-GHz support
- IR tools
- File browser (Archive)
- More polished UI & animations

---

Made with ❤️ by ttmolly + Grok
```

Save the file, then push it to GitHub:

```bash
git add README.md
git commit -m "Add README"
git push
```
