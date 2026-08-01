# PiSugar 3 Plus — Custom Button Setup

Configures the PiSugar 3 Plus custom function button (next to USB-C) to
control KeyCrow on a Pi 3 A+ running Raspberry Pi OS Trixie.

## Button mapping
- Single tap  -> start_keycrow.sh   (no-op if already running)
- Double tap  -> stop_keycrow.sh    (graceful SIGTERM, SIGKILL fallback, clears OLED)
- Long tap    -> sudo shutdown -h now (set directly via pisugar-server, no script)

## Set via pisugar-server socket:
```bash
echo "set_button_shell single /home/keycrow/keycrow/scripts/pisugar-button/start_keycrow.sh" | nc -U -q 1 /tmp/pisugar-server.sock
echo "set_button_shell double /home/keycrow/keycrow/scripts/pisugar-button/stop_keycrow.sh" | nc -U -q 1 /tmp/pisugar-server.sock
echo "set_button_shell long sudo shutdown -h now" | nc -U -q 1 /tmp/pisugar-server.sock
echo "set_button_enable single 1" | nc -U -q 1 /tmp/pisugar-server.sock
echo "set_button_enable double 1" | nc -U -q 1 /tmp/pisugar-server.sock
echo "set_button_enable long 1" | nc -U -q 1 /tmp/pisugar-server.sock
```

## Debugging notes (things that bit us)
- **Missing I2C address `0x68`**: PiSugar 3 (Plus) should show *both*
  `0x57` and `0x68` on `i2cdetect -y 1`. If `0x68` is missing/all-`XX` on
  `i2cdump`, it's a pogo-pin contact issue — fully power off, reseat the
  board firmly, power back on, recheck. This alone can cause flaky/dead
  button-tap detection.
- **`double_tap_enable` defaults to `false`** even if `double_tap_shell`
  is set. Must explicitly run `set_button_enable double 1` — the web UI
  and the daemon don't always keep this obviously visible.
- **Socket protocol quirk**: `set_` commands use an underscore
  (`set_button_enable`), but `get` commands use a space
  (`get button_enable single`, not `get_button_enable`).
- **pisugar-server runs as root** (`systemctl show pisugar-server -p User`
  returns empty = root default). Scripts run manually as your normal user
  will hit permission errors on `/tmp/pisugar-btn.log` and on `pkill`ing a
  root-owned process — always test with `sudo` to match real conditions.
- **OLED (SSD1306, I2C addr `0x3D` on this build) doesn't clear itself**
  when the process is killed — the display holds its own last frame in
  controller memory. `stop_keycrow.sh` explicitly clears it via
  `luma.oled` after killing the process.
- **Live debugging tip**: watch real tap events with
  `sudo journalctl -u pisugar-server -f -o cat | grep -iE "tap|button|shell|exec"`
