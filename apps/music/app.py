from core.app import BaseApp
import ui.music_menu as music_menu
import ui.music_player as music_player
import ui.bt_status as bt_status
from apps.music.player import (
    Player,
    list_tracks,
    set_output,
    BluetoothScanner,
    BluetoothConnector,
)
import core.config as config

OUTPUT_MODES = ["auto", "aux", "bluetooth"]


class MusicApp(BaseApp):
    name = "music"

    def __init__(self):
        self.selected = 0
        self.scroll_offset = 0
        self.tracks = []
        self.mode = "browse"
        self.player = Player()
        self.output_mode = "auto"

        self._dots = 0
        self.scanner = None
        self.connector = None
        self.bt_devices = []
        self.bt_selected = 0
        self.bt_scroll_offset = 0
        self._bt_pending_mac = None
        self._bt_pending_name = None

    def on_enter(self):
        self.tracks = list_tracks()
        self.selected = 0
        self.scroll_offset = 0
        self.mode = "browse"
        cfg = config.load()
        self.output_mode = cfg.get("music", {}).get("output", "auto")

    def on_exit(self):
        self.player.stop()

    def draw(self, device):
        if self.mode == "playing":
            self._draw_playing(device)
        elif self.mode == "bt_scan":
            self._draw_bt_scan(device)
        elif self.mode == "bt_list":
            self._draw_bt_list(device)
        elif self.mode == "bt_connect":
            self._draw_bt_connect(device)
        elif self.mode == "bt_confirm":
            self._draw_bt_confirm(device)
        elif self.mode == "bt_result":
            self._draw_bt_result(device)
        else:
            self.scroll_offset = music_menu.draw(
                device, self._labels(), self.selected, self.scroll_offset
            )

    def _draw_playing(self, device):
        if self.player.finished() and not self.player.is_paused():
            self._play_next()
        music_player.draw(
            device, self.player.current_track(), self.player.is_paused()
        )

    def _draw_bt_scan(self, device):
        self._dots = (self._dots + 1) % 4
        bt_status.draw(device, "Bluetooth", "Scanning" + "." * self._dots, "hold tight...")
        if self.scanner and self.scanner.done:
            self.bt_devices = self.scanner.result
            self.bt_selected = 0
            self.bt_scroll_offset = 0
            self.mode = "bt_list"

    def _draw_bt_list(self, device):
        self.bt_scroll_offset = music_menu.draw(
            device, self._bt_labels(), self.bt_selected, self.bt_scroll_offset,
            title="Pick device",
        )

    def _draw_bt_connect(self, device):
        # Switch to confirm UI if BlueZ asks for a PIN
        if self.connector and self.connector.needs_confirm:
            self.mode = "bt_confirm"
            return

        self._dots = (self._dots + 1) % 4
        bt_status.draw(
            device, "Bluetooth", "Connecting" + "." * self._dots,
            self._bt_pending_name or "",
        )
        if self.connector and self.connector.done:
            if self.connector.success:
                cfg = config.load()
                cfg.setdefault("music", {})
                cfg["music"]["bt_mac"] = self._bt_pending_mac
                cfg["music"]["output"] = "bluetooth"
                config.save(cfg)
                self.output_mode = "bluetooth"
            self.mode = "bt_result"

    def _draw_bt_confirm(self, device):
        pin = self.connector.passkey if self.connector else ""
        msg = f"PIN {pin}" if pin else "Confirm pair?"
        bt_status.draw(
            device, "Confirm?", msg, "L=No  R=Yes"
        )
        # If user already answered and connect finished, move on
        if self.connector and self.connector.done:
            if self.connector.success:
                cfg = config.load()
                cfg.setdefault("music", {})
                cfg["music"]["bt_mac"] = self._bt_pending_mac
                cfg["music"]["output"] = "bluetooth"
                config.save(cfg)
                self.output_mode = "bluetooth"
            self.mode = "bt_result"

    def _draw_bt_result(self, device):
        if self.connector and self.connector.success:
            if self.connector.audio_ok:
                bt_status.draw(device, "Bluetooth", "Connected!", "Audio OK")
            else:
                bt_status.draw(device, "Bluetooth", "Paired", "No audio sink")
        else:
            bt_status.draw(device, "Bluetooth", "Connection failed", "OK to continue")

    def _labels(self):
        names = [t[:-4] if t.lower().endswith(".mp3") else t for t in self.tracks]
        return names + [f"Output: {self.output_mode}", "Pair Bluetooth", "Back"]

    def _play_next(self):
        if not self.tracks:
            self.mode = "browse"
            return
        self.selected = (self.selected + 1) % len(self.tracks)
        self.player.play(self.tracks[self.selected])

    def _play_prev(self):
        if not self.tracks:
            return
        self.selected = (self.selected - 1) % len(self.tracks)
        self.player.play(self.tracks[self.selected])

    def _cycle_output(self):
        idx = OUTPUT_MODES.index(self.output_mode) if self.output_mode in OUTPUT_MODES else 0
        self.output_mode = OUTPUT_MODES[(idx + 1) % len(OUTPUT_MODES)]
        cfg = config.load()
        cfg.setdefault("music", {})
        cfg["music"]["output"] = self.output_mode
        config.save(cfg)
        if self.output_mode in ("aux", "auto"):
            set_output(self.output_mode)

    def _start_scan(self):
        self.scanner = BluetoothScanner()
        self.scanner.start(timeout=10)
        self._dots = 0
        self.mode = "bt_scan"

    def _bt_labels(self):
        names = [name for _, name in self.bt_devices]
        if not names:
            names = ["No devices found"]
        return names + ["Back"]

    def handle_input(self, button: str):
        if self.mode == "playing":
            return self._handle_playing(button)
        if self.mode == "bt_scan":
            return self._handle_bt_scan(button)
        if self.mode == "bt_list":
            return self._handle_bt_list(button)
        if self.mode == "bt_connect":
            return self._handle_bt_connect(button)
        if self.mode == "bt_confirm":
            return self._handle_bt_confirm(button)
        if self.mode == "bt_result":
            return self._handle_bt_result(button)
        return self._handle_browse(button)

    def _handle_browse(self, button):
        labels = self._labels()
        max_idx = len(labels) - 1

        if button == "UP":
            self.selected = (self.selected - 1) % (max_idx + 1)
            return None
        if button == "DOWN":
            self.selected = (self.selected + 1) % (max_idx + 1)
            return None
        if button == "OK":
            if self.selected < len(self.tracks):
                self.player.play(self.tracks[self.selected])
                self.mode = "playing"
                return None
            choice = labels[self.selected]
            if choice.startswith("Output"):
                self._cycle_output()
                return None
            if choice == "Pair Bluetooth":
                self._start_scan()
                return None
            if choice == "Back":
                return "back"
            return None
        if button == "BACK":
            return "back"
        return None

    def _handle_playing(self, button):
        if button == "OK":
            self.player.toggle_pause()
            return None
        if button == "RIGHT":
            self._play_next()
            return None
        if button == "LEFT":
            self._play_prev()
            return None
        if button == "BACK":
            self.player.stop()
            self.mode = "browse"
            return None
        return None

    def _handle_bt_scan(self, button):
        if button == "BACK":
            self.mode = "browse"
        return None

    def _handle_bt_list(self, button):
        labels = self._bt_labels()
        max_idx = len(labels) - 1

        if button == "UP":
            self.bt_selected = (self.bt_selected - 1) % (max_idx + 1)
            return None
        if button == "DOWN":
            self.bt_selected = (self.bt_selected + 1) % (max_idx + 1)
            return None
        if button == "OK":
            choice = labels[self.bt_selected]
            if choice in ("Back", "No devices found"):
                self.mode = "browse"
                return None
            mac, name = self.bt_devices[self.bt_selected]
            self._bt_pending_mac = mac
            self._bt_pending_name = name
            self.connector = BluetoothConnector()
            self.connector.start(mac)
            self._dots = 0
            self.mode = "bt_connect"
            return None
        if button == "BACK":
            self.mode = "browse"
            return None
        return None

    def _handle_bt_connect(self, button):
        if button == "BACK":
            self.mode = "browse"
        return None

    def _handle_bt_confirm(self, button):
        if not self.connector:
            self.mode = "browse"
            return None
        if button == "RIGHT":
            self.connector.answer(True)
            self.mode = "bt_connect"
            return None
        if button in ("LEFT", "BACK"):
            self.connector.answer(False)
            self.mode = "bt_result"
            return None
        return None

    def _handle_bt_result(self, button):
        if button in ("OK", "BACK"):
            self.mode = "browse"
        return None
