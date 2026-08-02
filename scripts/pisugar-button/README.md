# PiSugar 3 Plus — Custom Button + Boot Autostart

Configures the PiSugar 3 Plus custom function button (next to USB-C) to
control KeyCrow, and sets KeyCrow to auto-start on boot, on a Pi 3 A+
running Raspberry Pi OS Trixie.

## Button mapping
- Single tap  -> start_keycrow.sh   (no-op if already running)
- Double tap  -> stop_keycrow.sh    (graceful SIGTERM, SIGKILL fallback, clears OLED)
- Long tap    -> currently disabled (see "Known issues" below)

## Boot autostart
`keycrow.service` launches KeyCrow automatically on boot via systemd,
running as root to match how the button-triggered scripts run it.

Install:
```bash
sudo cp keycrow.service /etc/systemd/system/keycrow.service
sudo systemctl daemon-reload
sudo systemctl enable keycrow.service
sudo systemctl start keycrow.service
```

Useful commands:
```bash
sudo systemctl restart keycrow.service   # after code changes
sudo systemctl stop keycrow.service
sudo systemctl start keycrow.service
systemctl status keycrow.service
sudo journalctl -u keycrow.service -f -o cat   # live log
```

If you edit the `.service` file itself (not `keycrow.py`), run
`sudo systemctl daemon-reload` before restarting, or changes won't apply.

## Set button config via pisugar-server socket:
```bash
echo "set_button_shell single /home/keycrow/keycrow/scripts/pisugar-button/start_keycrow.sh" | nc -U -q 1 /tmp/pisugar-server.sock
echo "set_button_shell double /home/keycrow/keycrow/scripts/pisugar-button/stop_keycrow.sh" | nc -U -q 1 /tmp/pisugar-server.sock
echo "set_button_enable single 1" | nc -U -q 1 /tmp/pisugar-server.sock
echo "set_button_enable double 1" | nc -U -q 1 /tmp/pisugar-server.sock
```

## Known issues
- **Long tap (shutdown) currently disabled.** Accidental triggers were
  happening during normal single-tap use. Root cause is believed to be
  mechanical button bounce (a single physical press occasionally
  registering as multiple electrical contacts), which the PiSugar MCU
  can misread as a different tap type. This is a hardware/firmware-level
  behavior, not something fixable in our scripts, since our shell
  commands only run *after* the daemon has already classified the tap.
  Re-enable with:
```bash
  echo "set_button_shell long sudo shutdown -h now" | nc -U -q 1 /tmp/pisugar-server.sock
  echo "set_button_enable long 1" | nc -U -q 1 /tmp/pisugar-server.sock
```

## Debugging notes (things that bit us)
- **Missing I2C address `0x68`**: PiSugar 3 (Plus) should show *both*
  `0x57` and `0x68` on `i2cdetect -y 1`. If `0x68` is missing/all-`XX` on
  `i2cdump`, it's a pogo-pin contact issue — fully power off, reseat the
  board firmly, power back on, recheck. This alone caused dead/flaky
  button-tap detection for us.
- **`double_tap_enable` defaults to `false`** even if `double_tap_shell`
  is set. Must explicitly run `set_button_enable double 1`.
- **Socket protocol quirk**: `set_` commands use an underscore
  (`set_button_enable`), but `get` commands use a space
  (`get button_enable single`, not `get_button_enable`).
- **pisugar-server runs as root** (`systemctl show pisugar-server -p User`
  returns empty = root default). Test scripts with `sudo` to match real
  conditions — manual non-sudo runs will hit permission errors on
  `/tmp/pisugar-btn.log` and on `pkill`ing a root-owned process.
- **OLED (SSD1306, I2C addr `0x3D` on this build) doesn't clear itself**
  when the process is killed — it holds its own last frame in controller
  memory. `stop_keycrow.sh` explicitly clears it via `luma.oled`.
- **After moving/renaming script files**, remember the daemon's config
  still points at the *old* path until you re-run `set_button_shell`
  with the new one — taps will still show as "triggered" in the web UI
  even though the shell command silently fails to find the file.
- **GPIO conflict**: only one process can hold KeyCrow's button GPIO pin
  at a time. If you manually start KeyCrow (e.g. via `sudo
  start_keycrow.sh`) and then also try starting `keycrow.service`, the
  second one fails with `lgpio.error: 'GPIO busy'`. Always `pkill -f
  "python.*keycrow.py"` before starting via a different method.
- **Live debugging tip**: watch real tap events with
  `sudo journalctl -u pisugar-server -f -o cat | grep -iE "tap|button|shell|exec"`
