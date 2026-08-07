from core.app import BaseApp
import ui.music_menu as music_menu
import ui.music_player as music_player
import ui.bt_status as bt_status
from apps.music.player import (
    Player,
    list_tracks,
    list_library,
    list_paired_devices,
    set_output,
    get_volume,
    set_volume,
    BluetoothScanner,
    BluetoothConnector,
)
import core.config as config
from pathlib import Path

OUTPUT_MODES = ["auto", "aux", "bluetooth"]


class MusicApp(BaseApp):
    name = "music"

    def __init__(self):
        self.selected = 0
        self.scroll_offset = 0
        self.mode = "browse"
        self.player = Player()
        self.output_mode = "auto"

        self.lib_path = ""
        self.lib_items = []
        self.lib_selected = 0
        self.lib_scroll = 0
        self._return_mode = "browse"
        self._return_path = ""
        self._return_selected = 0
        self._return_scroll = 0
        self.tracks = []

        self._dots = 0
        self.scanner = None
        self.connector = None
        self.bt_devices = []
        self.bt_selected = 0
        self.bt_scroll_offset = 0
        self._bt_pending_mac = None
        self._bt_pending_name = None
        self.paired_devices = []

    def on_enter(self):
        self.selected = 0
        self.scroll_offset = 0
        self.mode = "browse"
        self.lib_path = ""
        cfg = config.load()
        self.output_mode = cfg.get("music", {}).get("output", "auto")

        # Restore last volume
        vol = cfg.get("music", {}).get("volume", 80)
        set_volume(vol)

        if self.output_mode in ("aux", "auto"):
            set_output(self.output_mode)

    def on_exit(self):
        self.player.stop()

    def draw(self, device):
        if self.mode == "playing":
            self._draw_playing(device)
        elif self.mode == "library":
            self._draw_library(device)
        elif self.mode == "bt_menu":
            self.scroll_offset = music_menu.draw(
                device, self._bt_menu_labels(), self.selected, self.scroll_offset,
                title="Bluetooth",
            )
        elif self.mode == "bt_paired":
            self.bt_scroll_offset = music_menu.draw(
                device, self._paired_labels(), self.bt_selected, self.bt_scroll_offset,
                title="My Devices",
            )
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
                device, self._top_labels(), self.selected, self.scroll_offset,
                title="Music",
            )

    def _draw_playing(self, device):
        if self.player.finished() and not self.player.is_paused():
            self._play_next()
        music_player.draw(
            device,
            self.player.current_track(),
            self.player.is_paused(),
            elapsed=self.player.elapsed(),
            duration=self.player.duration(),
            volume=get_volume(),
            output_mode=self.output_mode,
        )

    def _draw_library(self, device):
        title = "Library" if not self.lib_path else Path(self.lib_path).name
        self.lib_scroll = music_menu.draw(
            device, self._lib_labels(), self.lib_selected, self.lib_scroll,
            title=title,
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
        bt_status.draw(device, "Confirm?", msg, "L=No  R=Yes")
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

    def _top_labels(self):
        return ["Library", f"Output: {self.output_mode}", "Bluetooth", "Back"]

    def _lib_labels(self):
        labels = []
        for item in self.lib_items:
            if item["is_dir"]:
                labels.append(item["name"] + "/")
            else:
                name = item["name"]
                if name.lower().endswith(".mp3"):
                    name = name[:-4]
                labels.append(name)
        labels.append("Back")
        return labels

    def _bt_menu_labels(self):
        return ["Connect new device", "My Devices", "Back"]

    def _paired_labels(self):
        if not self.paired_devices:
            return ["No paired devices", "Back"]
        return [name for _, name in self.paired_devices] + ["Back"]

    def _bt_labels(self):
        names = [name for _, name in self.bt_devices]
        if not names:
            names = ["No devices found"]
        return names + ["Back"]

    def _open_library(self, rel_path=""):
        self.lib_path = rel_path
        self.lib_items = list_library(rel_path)
        self.tracks = [i["rel"] for i in self.lib_items if not i["is_dir"]]
        self.lib_selected = 0
        self.lib_scroll = 0
        self.mode = "library"

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

    def _ensure_output(self):
        if self.output_mode in ("aux", "auto"):
            set_output(self.output_mode)

    def _play_next(self):
        if not self.tracks:
            self.mode = self._return_mode
            return
        cur = self.player.current_track()
        idx = 0
        for i, rel in enumerate(self.tracks):
            if Path(rel).name == cur:
                idx = i
                break
        idx = (idx + 1) % len(self.tracks)
        self._ensure_output()
        self.player.play(self.tracks[idx])

    def _play_prev(self):
        if not self.tracks:
            return
        cur = self.player.current_track()
        idx = 0
        for i, rel in enumerate(self.tracks):
            if Path(rel).name == cur:
                idx = i
                break
        idx = (idx - 1) % len(self.tracks)
        self._ensure_output()
        self.player.play(self.tracks[idx])

    def handle_input(self, button: str):
        if self.mode == "playing":
            return self._handle_playing(button)
        if self.mode == "library":
            return self._handle_library(button)
        if self.mode == "bt_menu":
            return self._handle_bt_menu(button)
        if self.mode == "bt_paired":
            return self._handle_bt_paired(button)
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
        labels = self._top_labels()
        max_idx = len(labels) - 1
        if button == "UP":
            self.selected = (self.selected - 1) % (max_idx + 1)
            return None
        if button == "DOWN":
            self.selected = (self.selected + 1) % (max_idx + 1)
            return None
        if button == "OK":
            choice = labels[self.selected]
            if choice == "Library":
                self._open_library("")
                return None
            if choice.startswith("Output"):
                self._cycle_output()
                return None
            if choice == "Bluetooth":
                self.selected = 0
                self.scroll_offset = 0
                self.mode = "bt_menu"
                return None
            if choice == "Back":
                return "back"
            return None
        if button == "BACK":
            return "back"
        return None

    def _handle_library(self, button):
        labels = self._lib_labels()
        max_idx = len(labels) - 1
        if button == "UP":
            self.lib_selected = (self.lib_selected - 1) % (max_idx + 1)
            return None
        if button == "DOWN":
            self.lib_selected = (self.lib_selected + 1) % (max_idx + 1)
            return None
        if button == "OK":
            if self.lib_selected >= len(self.lib_items):
                if self.lib_path:
                    parent = str(Path(self.lib_path).parent)
                    if parent == ".":
                        parent = ""
                    self._open_library(parent)
                else:
                    self.selected = 0
                    self.scroll_offset = 0
                    self.mode = "browse"
                return None

            item = self.lib_items[self.lib_selected]
            if item["is_dir"]:
                self._open_library(item["rel"])
                return None

            self._return_mode = "library"
            self._return_path = self.lib_path
            self._return_selected = self.lib_selected
            self._return_scroll = self.lib_scroll
            self._ensure_output()
            self.player.play(item["rel"])
            self.mode = "playing"
            return None

        if button == "BACK":
            if self.lib_path:
                parent = str(Path(self.lib_path).parent)
                if parent == ".":
                    parent = ""
                self._open_library(parent)
            else:
                self.selected = 0
                self.scroll_offset = 0
                self.mode = "browse"
            return None
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
        if button == "UP":
            set_volume(get_volume() + 5)
            return None
        if button == "DOWN":
            set_volume(get_volume() - 5)
            return None
        if button == "BACK":
            self.player.stop()
            if self._return_mode == "library":
                self._open_library(self._return_path)
                self.lib_selected = self._return_selected
                self.lib_scroll = self._return_scroll
            else:
                self.mode = "browse"
            return None
        return None

    def _handle_bt_menu(self, button):
        labels = self._bt_menu_labels()
        max_idx = len(labels) - 1
        if button == "UP":
            self.selected = (self.selected - 1) % (max_idx + 1)
            return None
        if button == "DOWN":
            self.selected = (self.selected + 1) % (max_idx + 1)
            return None
        if button == "OK":
            choice = labels[self.selected]
            if choice == "Connect new device":
                self._start_scan()
                return None
            if choice == "My Devices":
                self.paired_devices = list_paired_devices()
                self.bt_selected = 0
                self.bt_scroll_offset = 0
                self.mode = "bt_paired"
                return None
            if choice == "Back":
                self.selected = 0
                self.scroll_offset = 0
                self.mode = "browse"
                return None
            return None
        if button == "BACK":
            self.selected = 0
            self.scroll_offset = 0
            self.mode = "browse"
            return None
        return None

    def _handle_bt_paired(self, button):
        labels = self._paired_labels()
        max_idx = len(labels) - 1
        if button == "UP":
            self.bt_selected = (self.bt_selected - 1) % (max_idx + 1)
            return None
        if button == "DOWN":
            self.bt_selected = (self.bt_selected + 1) % (max_idx + 1)
            return None
        if button == "OK":
            choice = labels[self.bt_selected]
            if choice in ("Back", "No paired devices"):
                self.selected = 0
                self.scroll_offset = 0
                self.mode = "bt_menu"
                return None
            mac, name = self.paired_devices[self.bt_selected]
            self._bt_pending_mac = mac
            self._bt_pending_name = name
            self.connector = BluetoothConnector()
            self.connector.start(mac)
            self._dots = 0
            self.mode = "bt_connect"
            return None
        if button == "BACK":
            self.selected = 0
            self.scroll_offset = 0
            self.mode = "bt_menu"
            return None
        return None

    def _handle_bt_scan(self, button):
        if button == "BACK":
            self.mode = "bt_menu"
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
                self.mode = "bt_menu"
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
            self.mode = "bt_menu"
            return None
        return None

    def _handle_bt_connect(self, button):
        if button == "BACK":
            self.mode = "bt_menu"
        return None

    def _handle_bt_confirm(self, button):
        if not self.connector:
            self.mode = "bt_menu"
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
            self.selected = 0
            self.scroll_offset = 0
            self.mode = "browse"
        return None
