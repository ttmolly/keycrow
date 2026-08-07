import os
import subprocess
import signal
import re
import threading
import time
from pathlib import Path

MUSIC_DIR = Path.home() / "keycrow" / "music"
DEVICE_RE = re.compile(r"Device\s+([0-9A-Fa-f:]{17})\s+(.+)$")

WP_CONF_DIR = Path.home() / ".config" / "wireplumber" / "wireplumber.conf.d"
WP_CONF_FILE = WP_CONF_DIR / "50-bluez-headless.conf"
WP_CONF_TEXT = """wireplumber.profiles = {
  main = {
    monitor.bluez.seat-monitoring = disabled
  }
}

monitor.bluez.properties = {
  bluez5.roles = [ a2dp_sink a2dp_source hsp_hs hfp_hf ]
}
"""


def list_tracks(rel_path=""):
    folder = MUSIC_DIR / rel_path if rel_path else MUSIC_DIR
    if not folder.exists():
        folder.mkdir(parents=True, exist_ok=True)
        return []
    return sorted(p.name for p in folder.glob("*.mp3"))


def list_library(rel_path=""):
    folder = MUSIC_DIR / rel_path if rel_path else MUSIC_DIR
    if not folder.exists():
        folder.mkdir(parents=True, exist_ok=True)
        return []

    items = []
    for p in sorted(folder.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
        if p.name.startswith("."):
            continue
        if p.is_dir():
            rel = str(Path(rel_path) / p.name) if rel_path else p.name
            items.append({"name": p.name, "is_dir": True, "rel": rel})
        elif p.suffix.lower() == ".mp3":
            rel = str(Path(rel_path) / p.name) if rel_path else p.name
            items.append({"name": p.name, "is_dir": False, "rel": rel})
    return items


def list_paired_devices():
    """Return list of (mac, name) for paired Bluetooth devices."""
    found = {}
    commands = (
        ["bluetoothctl", "devices", "Paired"],
        ["bluetoothctl", "paired-devices"],
        ["bluetoothctl", "devices"],
    )
    for cmd in commands:
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=8,
            )
        except Exception:
            continue
        for line in (result.stdout or "").splitlines():
            m = DEVICE_RE.match(line.strip())
            if not m:
                continue
            mac, name = m.group(1), m.group(2).strip()
            found[mac] = name
        if found and cmd != ["bluetoothctl", "devices"]:
            break
    return sorted(found.items(), key=lambda kv: kv[1].lower())


def get_duration(path: Path) -> float:
    try:
        out = subprocess.check_output(
            [
                "ffprobe", "-v", "quiet",
                "-show_entries", "format=duration",
                "-of", "csv=p=0",
                str(path),
            ],
            text=True,
            timeout=5,
            stderr=subprocess.DEVNULL,
        ).strip()
        if out:
            return max(0.0, float(out))
    except Exception:
        pass
    try:
        from mutagen.mp3 import MP3
        audio = MP3(str(path))
        if audio and audio.info:
            return max(0.0, float(audio.info.length))
    except Exception:
        pass
    return 0.0


def get_volume() -> int:
    try:
        out = subprocess.check_output(
            ["amixer", "sget", "Master"],
            text=True,
            timeout=3,
            stderr=subprocess.DEVNULL,
        )
        m = re.search(r"\[(\d+)%\]", out)
        if m:
            return max(0, min(100, int(m.group(1))))
    except Exception:
        pass
    try:
        out = subprocess.check_output(
            ["pactl", "get-sink-volume", "@DEFAULT_SINK@"],
            text=True,
            timeout=3,
            stderr=subprocess.DEVNULL,
        )
        m = re.search(r"(\d+)%", out)
        if m:
            return max(0, min(100, int(m.group(1))))
    except Exception:
        pass
    return 80


def set_volume(percent: int) -> int:
    percent = max(0, min(100, int(percent)))
    for control in ("Master", "PCM", "Headphone"):
        subprocess.run(
            ["amixer", "sset", control, f"{percent}%", "unmute"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    try:
        subprocess.run(
            ["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{percent}%"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=3,
        )
        subprocess.run(
            ["pactl", "set-sink-mute", "@DEFAULT_SINK@", "0"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=3,
        )
    except Exception:
        pass
    try:
        import core.config as config
        cfg = config.load()
        cfg.setdefault("music", {})
        cfg["music"]["volume"] = percent
        config.save(cfg)
    except Exception:
        pass
    return percent


class Player:
    def __init__(self):
        self._proc = None
        self._track = None
        self._paused = False
        self._duration = 0.0
        self._play_started = 0.0
        self._total_paused = 0.0
        self._pause_started = None

    def play(self, filename: str) -> bool:
        self.stop()
        path = MUSIC_DIR / filename
        if not path.exists():
            return False
        self._duration = get_duration(path)
        self._play_started = time.monotonic()
        self._total_paused = 0.0
        self._pause_started = None
        self._proc = subprocess.Popen(
            ["mpg123", "-q", str(path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        self._track = path.name
        self._paused = False
        return True

    def toggle_pause(self):
        if self._proc is None:
            return
        if self._paused:
            self._proc.send_signal(signal.SIGCONT)
            if self._pause_started is not None:
                self._total_paused += time.monotonic() - self._pause_started
                self._pause_started = None
            self._paused = False
        else:
            self._proc.send_signal(signal.SIGSTOP)
            self._pause_started = time.monotonic()
            self._paused = True

    def is_paused(self) -> bool:
        return self._paused

    def stop(self):
        if self._proc is not None:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=1)
            except subprocess.TimeoutExpired:
                self._proc.kill()
        self._proc = None
        self._track = None
        self._paused = False
        self._duration = 0.0
        self._play_started = 0.0
        self._total_paused = 0.0
        self._pause_started = None

    def current_track(self):
        return self._track

    def finished(self) -> bool:
        return self._proc is not None and self._proc.poll() is not None

    def duration(self) -> float:
        return self._duration

    def elapsed(self) -> float:
        if self._play_started <= 0:
            return 0.0
        if self._paused and self._pause_started is not None:
            t = self._pause_started - self._play_started - self._total_paused
        else:
            t = time.monotonic() - self._play_started - self._total_paused
        if self._duration > 0:
            t = min(t, self._duration)
        return max(0.0, t)


def set_output(mode: str):
    target = {"aux": "1", "hdmi": "2", "auto": "0"}.get(mode, "0")
    subprocess.run(
        ["amixer", "cset", "numid=3", target],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        import core.config as config
        vol = config.load().get("music", {}).get("volume", 80)
    except Exception:
        vol = 80
    vol = max(0, min(100, int(vol)))
    for control in ("Master", "PCM", "Headphone"):
        subprocess.run(
            ["amixer", "sset", control, f"{vol}%", "unmute"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    if mode == "bluetooth":
        return
    try:
        out = subprocess.check_output(
            ["pactl", "list", "short", "sinks"],
            text=True,
            timeout=5,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        return
    sinks = []
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 2:
            sinks.append(parts[1])
    if not sinks:
        return
    chosen = None
    if mode == "aux":
        for name in sinks:
            low = name.lower()
            if "bluez" in low or "hdmi" in low:
                continue
            if any(k in low for k in (
                "bcm2835", "headphones", "analog",
                "stereo-fallback", "avjack", "mailbox"
            )):
                chosen = name
                break
        if chosen is None:
            for name in sinks:
                low = name.lower()
                if "bluez" not in low and "hdmi" not in low:
                    chosen = name
                    break
    elif mode == "hdmi":
        for name in sinks:
            if "hdmi" in name.lower() and "bluez" not in name.lower():
                chosen = name
                break
    else:
        try:
            default = subprocess.check_output(
                ["pactl", "get-default-sink"],
                text=True,
                timeout=3,
                stderr=subprocess.DEVNULL,
            ).strip()
            if default and "bluez" not in default.lower():
                chosen = default
        except Exception:
            pass
        if chosen is None:
            for name in sinks:
                if "bluez" not in name.lower():
                    chosen = name
                    break
    if chosen:
        subprocess.run(
            ["pactl", "set-default-sink", chosen],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
        subprocess.run(
            ["pactl", "set-sink-volume", chosen, f"{vol}%"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
        subprocess.run(
            ["pactl", "set-sink-mute", chosen, "0"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5,
        )


def ensure_headless_bt_audio() -> bool:
    try:
        WP_CONF_DIR.mkdir(parents=True, exist_ok=True)
        need_restart = False
        if not WP_CONF_FILE.exists() or WP_CONF_FILE.read_text() != WP_CONF_TEXT:
            WP_CONF_FILE.write_text(WP_CONF_TEXT)
            need_restart = True
        env = os.environ.copy()
        if "XDG_RUNTIME_DIR" not in env:
            env["XDG_RUNTIME_DIR"] = f"/run/user/{os.getuid()}"
        subprocess.run(
            ["systemctl", "--user", "start", "pipewire", "pipewire-pulse", "wireplumber"],
            capture_output=True,
            timeout=10,
            env=env,
        )
        if need_restart:
            subprocess.run(
                ["systemctl", "--user", "restart", "pipewire", "pipewire-pulse", "wireplumber"],
                capture_output=True,
                timeout=15,
                env=env,
            )
            time.sleep(2)
        return True
    except Exception as e:
        print(f"[bt] ensure_headless_bt_audio failed: {e}")
        return False


def connect_bluetooth(mac: str) -> bool:
    if not mac:
        return False
    try:
        result = subprocess.run(
            ["bluetoothctl", "connect", mac],
            capture_output=True,
            text=True,
            timeout=20,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False
    return "Connection successful" in (result.stdout or "")


def set_bluetooth_audio(mac: str) -> bool:
    mac_id = mac.replace(":", "_").upper()
    time.sleep(1.5)
    try:
        out = subprocess.check_output(
            ["pactl", "list", "short", "sinks"],
            text=True,
            timeout=5,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        out = ""
    sink = None
    for line in out.splitlines():
        if "bluez" in line.lower() and mac_id in line.upper().replace(":", "_"):
            parts = line.split()
            if len(parts) >= 2:
                sink = parts[1]
                break
    if sink is None:
        for line in out.splitlines():
            if "bluez_output" in line.lower():
                parts = line.split()
                if len(parts) >= 2:
                    sink = parts[1]
                    break
    if not sink:
        return False
    try:
        import core.config as config
        vol = config.load().get("music", {}).get("volume", 80)
    except Exception:
        vol = 80
    vol = max(0, min(100, int(vol)))
    try:
        subprocess.run(
            ["pactl", "set-default-sink", sink],
            capture_output=True,
            timeout=5,
        )
        subprocess.run(
            ["pactl", "set-sink-volume", sink, f"{vol}%"],
            capture_output=True,
            timeout=5,
        )
        subprocess.run(
            ["pactl", "set-sink-mute", sink, "0"],
            capture_output=True,
            timeout=5,
        )
        return True
    except Exception:
        return False


def _lookup_name(mac: str):
    try:
        result = subprocess.run(
            ["bluetoothctl", "info", mac],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None
    for line in result.stdout.splitlines():
        line = line.strip()
        if line.startswith("Name:"):
            return line.split("Name:", 1)[1].strip()
        if line.startswith("Alias:"):
            return line.split("Alias:", 1)[1].strip()
    return None


def scan_devices(timeout=10):
    ensure_headless_bt_audio()
    try:
        subprocess.run(
            ["bluetoothctl", "power", "on"],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except Exception:
        pass
    found = {}
    try:
        proc = subprocess.Popen(
            ["bluetoothctl"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
    except FileNotFoundError:
        return []

    def send(cmd):
        try:
            proc.stdin.write(cmd + "\n")
            proc.stdin.flush()
        except Exception:
            pass

    send("scan on")
    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(0.4)
        try:
            result = subprocess.run(
                ["bluetoothctl", "devices"],
                capture_output=True,
                text=True,
                timeout=3,
            )
            for line in result.stdout.splitlines():
                m = DEVICE_RE.match(line.strip())
                if not m:
                    continue
                mac, name = m.group(1), m.group(2).strip()
                if name.startswith("LE_"):
                    continue
                if name and name != mac.replace(":", "-"):
                    found[mac] = name
                elif mac not in found:
                    found[mac] = name
        except Exception:
            pass
    send("scan off")
    send("quit")
    try:
        proc.communicate(timeout=3)
    except Exception:
        proc.kill()
    resolved = {}
    for mac, name in found.items():
        if name.replace("-", ":").upper() == mac.upper() or name == mac.replace(":", "-"):
            better = _lookup_name(mac)
            resolved[mac] = better or name
        else:
            resolved[mac] = name
    return sorted(resolved.items(), key=lambda kv: kv[1].lower())


class BluetoothScanner:
    def __init__(self):
        self.done = False
        self.result = []
        self._thread = None

    def start(self, timeout=10):
        self.done = False
        self.result = []
        self._thread = threading.Thread(target=self._run, args=(timeout,), daemon=True)
        self._thread.start()

    def _run(self, timeout):
        self.result = scan_devices(timeout)
        self.done = True


class BluetoothConnector:
    def __init__(self):
        self.done = False
        self.success = False
        self.audio_ok = False
        self.needs_confirm = False
        self.passkey = ""
        self._answer = None
        self._answer_event = threading.Event()
        self._thread = None

    def start(self, mac):
        self.done = False
        self.success = False
        self.audio_ok = False
        self.needs_confirm = False
        self.passkey = ""
        self._answer = None
        self._answer_event.clear()
        self._thread = threading.Thread(target=self._run, args=(mac,), daemon=True)
        self._thread.start()

    def answer(self, yes: bool):
        self._answer = yes
        self.needs_confirm = False
        self._answer_event.set()

    def _run(self, mac):
        ensure_headless_bt_audio()
        try:
            proc = subprocess.Popen(
                ["bluetoothctl"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
        except FileNotFoundError:
            self.done = True
            return

        def send(cmd):
            try:
                proc.stdin.write(cmd + "\n")
                proc.stdin.flush()
            except Exception:
                pass

        lines = []

        def reader():
            try:
                for line in proc.stdout:
                    lines.append(line)
                    low = line.lower()
                    if (
                        "confirm passkey" in low
                        or "confirm pairing" in low
                        or "request confirmation" in low
                    ):
                        digits = re.findall(r"\d{4,6}", line)
                        self.passkey = digits[0] if digits else ""
                        self.needs_confirm = True
                        self._answer_event.clear()
                        if self._answer_event.wait(timeout=30):
                            send("yes" if self._answer else "no")
                        else:
                            send("no")
                            self.needs_confirm = False
                    elif "enter pin" in low or "request passkey" in low:
                        send("0000")
            except Exception:
                pass

        t = threading.Thread(target=reader, daemon=True)
        t.start()
        send("power on")
        time.sleep(0.5)
        send("agent on")
        time.sleep(0.5)
        send("default-agent")
        time.sleep(0.5)
        send(f"pair {mac}")
        time.sleep(12)
        if not self._answer_event.is_set() and not self.needs_confirm:
            send("yes")
            time.sleep(1)
        send(f"trust {mac}")
        time.sleep(1.5)
        send(f"connect {mac}")
        time.sleep(5)
        send("quit")
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()
        out = "".join(lines)
        ok = "Connection successful" in out or "Pairing successful" in out
        if not ok:
            ok = connect_bluetooth(mac)
        self.success = ok
        if ok:
            self.audio_ok = set_bluetooth_audio(mac)
        self.done = True
