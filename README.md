# KeyCrow

**KeyCrow** is a DIY multi-tool inspired by the Flipper Zero, built for the Raspberry Pi.
It features a custom interface on a 1.3" OLED display with physical buttons, modular apps, and support for custom animated splash screens.

## Hardware

- Raspberry Pi 3 Model A+
- Adafruit 1.3" 128x64 OLED (SSD1306, I2C)
- 6 buttons (Up, Down, Left, Right, OK, Back)
- PiSugar 3 Plus UPS — powers the Pi and provides a custom function
  button wired to start/stop KeyCrow (see `scripts/pisugar-button/`)

## Features (Current)

- Animated splash screen system (custom + default)
- Main menu with clean UI
- WiFi Tools (basic network scanning)
- Settings menu (switch splash screens)
- Modular code structure
- Config system using `config.toml`
- Splash Manager for adding/converting custom animations
- Auto-starts on boot via systemd (`scripts/pisugar-button/keycrow.service`)
- PiSugar function button: single tap to start, double tap to stop
  cleanly (see `scripts/pisugar-button/README.md` for setup + debugging notes)

## Project Structure

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
    ├── splash_manager.py       # Tool to add new splashes
    └── scripts/
        └── pisugar-button/     # PiSugar button + boot autostart setup
            ├── start_keycrow.sh
            ├── stop_keycrow.sh
            ├── keycrow.service
            └── README.md

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

For PiSugar 3 Plus button control and boot autostart, see
[`scripts/pisugar-button/README.md`](scripts/pisugar-button/README.md).

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
