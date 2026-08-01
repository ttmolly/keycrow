import subprocess
import signal
import re
import threading
import time
from pathlib import Path

MUSIC_DIR = Path.home() / "keycrow" / "music"

DEVICE_RE = re.compile(r"Device\s+([0-9A-Fa-f:]{17})\s+(.+)$")
NAME_LINE_RE = re.compile(r"Device\s+([0-9A-Fa-f:]{17})\s+(Name|Alias):\s*(.+)$")
SKIP_PREFIXES = ("RSSI", "TxPower", "Name:", "Alias:", "Connected:", "Paired:", "Trusted:")


def list_tracks():
    """Return a sorted list of .mp3 filenames found in the music folder."""
    if not MUSIC_DIR.exists():
        MUSIC_DIR.mkdir(parents=True, exist_ok=True)
        return []
    return sorted(p.name for p in MUSIC_DIR.glob("*.mp3"))


class Player:
    """
    Thin wrapper around mpg123.
    One track plays at a time. Pause is done with SIGSTOP/SIGCONT so we
    don't need to speak mpg123's remote-control protocol.
    """

    def __init__(self):
        self._proc = None
        self._track = None
        self._paused = False

    def play(self, filename: str) -> bool:
        self.stop()
        path = MUSIC_DIR / filename
        if not path.exists():
            return False
        self._proc = subprocess.Popen(
            ["mpg123", "-q", str(path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        self._track = filename
        self._paused = False
        return True

    def toggle_pause(self):
        if self._proc is None:
            return
        if self._paused:
            self._proc.send_signal(signal.SIGCONT)
            self._paused = False
        else:
            self._proc.send_signal(signal.SIGSTOP)
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

    def current_track(self):
        return self._track

    def finished(self) -> bool:
        """True if a track was playing and has just ended on its own."""
        return self._proc is not None and self._proc.poll() is not None


def set_output(mode: str):
    """
    Force the Pi's built-in analog output.
    mode: 'aux' -> 3.5mm jack, 'hdmi' -> HDMI, 'auto' -> let ALSA decide.
    Bluetooth is handled separately since it isn't one of the built-in
    ALSA jack targets.
    """
    target = {"aux": "1", "hdmi": "2", "auto": "0"}.get(mode, "0")
    subprocess.run(
        ["amixer", "cset", "numid=3", target],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def connect_bluetooth(mac: str) -> bool:
    """
    Reconnects to an already-paired/trusted Bluetooth audio device.
    """
    if not mac:
        return False
    try:
        result = subprocess.run(
            ["bluetoothctl", "connect", mac],
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False
    return "Connection successful" in result.stdout


def _lookup_name(mac: str):
    """Ask bluetoothctl directly for a device's resolved Name/Alias."""
    try:
        result = subprocess.run(
            ["bluetoothctl", "info", mac],
            capture_output=True, text=True, timeout=5,
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
    """
    Scans for nearby Bluetooth devices for `timeout` seconds and returns
    a sorted list of (mac, name) tuples with real device names where
    available.

    bluetoothctl first reports a newly-seen device using a placeholder
    "name" that's just its MAC address with dashes instead of colons,
    then follows up with a separate line once the real name/alias is
    resolved. We track both and prefer the resolved one; for anything
    still stuck on the placeholder after scanning, we do one more
    explicit lookup via `bluetoothctl info`.

    Requires a reasonably recent bluez (Raspberry Pi OS Bookworm ships one
    new enough) for the non-interactive `bluetoothctl <cmd> <args>` form
    and the `--timeout` scan flag.
    """
    try:
        subprocess.run(
            ["bluetoothctl", "power", "on"],
            capture_output=True, text=True, timeout=5,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []

    output = ""
    try:
        result = subprocess.run(
            ["bluetoothctl", "--timeout", str(timeout), "scan", "on"],
            capture_output=True, text=True, timeout=timeout + 5,
        )
        output += result.stdout
    except subprocess.TimeoutExpired:
        pass
    except FileNotFoundError:
        return []

    try:
        result = subprocess.run(
            ["bluetoothctl", "devices"],
            capture_output=True, text=True, timeout=5,
        )
        output += "\n" + result.stdout
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    devices = {}
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if line.startswith("[NEW]") or line.startswith("[CHG]") or line.startswith("[DEL]"):
            line = line.split("]", 1)[1].strip()

        name_match = NAME_LINE_RE.match(line)
        if name_match:
            mac, _, name = name_match.groups()
            devices[mac] = name.strip()
            continue

        m = DEVICE_RE.match(line)
        if not m:
            continue
        mac, rest = m.group(1), m.group(2).strip()
        if rest.startswith(SKIP_PREFIXES):
            continue
        # Don't let a placeholder line clobber a name we already resolved.
        devices.setdefault(mac, rest)

    resolved = {}
    for mac, name in devices.items():
        looks_like_placeholder = name.replace("-", ":").upper() == mac.upper()
        if looks_like_placeholder:
            better = _lookup_name(mac)
            resolved[mac] = better or name
        else:
            resolved[mac] = name

    return sorted(resolved.items(), key=lambda kv: kv[1].lower())


def pair_device(mac: str, timeout=30) -> bool:
    """
    Pairs, trusts, and connects to a device that scan_devices() found.

    This runs as ONE persistent `bluetoothctl` session (via stdin/stdout
    pipes) rather than separate one-shot calls. Each separate
    `subprocess.run(["bluetoothctl", ...])` call is its own process, and
    an agent registered ("agent on") in one of those processes is gone
    the moment that process exits — so a later `pair` call has no agent
    around to answer any confirmation prompt, and pairing can fail even
    though the headset is sitting there in pairing mode. Keeping it all
    in one session keeps the agent alive the whole time.
    """
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
        return False

    def send(cmd, wait=2.0):
        try:
            proc.stdin.write(cmd + "\n")
            proc.stdin.flush()
        except (BrokenPipeError, ValueError):
            return
        time.sleep(wait)

    try:
        send("agent on")
        send("default-agent")
        send(f"pair {mac}", wait=5.0)
        # Auto-answer a "Confirm passkey ... (yes/no)" style prompt if
        # one showed up. Harmless no-op if nothing was waiting on input.
        send("yes", wait=2.0)
        send(f"trust {mac}", wait=2.0)
        send(f"connect {mac}", wait=3.0)
        send("quit", wait=1.0)
        out, _ = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        try:
            out, _ = proc.communicate(timeout=5)
        except Exception:
            out = ""
    except Exception:
        proc.kill()
        out = ""

    if "Connection successful" in out:
        return True

    # Fall back to a plain reconnect attempt in case connect succeeded
    # but the session output above was ambiguous.
    return connect_bluetooth(mac)


class BluetoothScanner:
    """Runs scan_devices() on a background thread so button input and the
    screen can keep updating while the scan (several seconds) runs."""

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
    """Runs pair_device() on a background thread for the same reason."""

    def __init__(self):
        self.done = False
        self.success = False
        self._thread = None

    def start(self, mac):
        self.done = False
        self.success = False
        self._thread = threading.Thread(target=self._run, args=(mac,), daemon=True)
        self._thread.start()

    def _run(self, mac):
        self.success = pair_device(mac)
        self.done = True
