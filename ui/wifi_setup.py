from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from luma.core.render import canvas
from PIL import ImageFont
from time import sleep
import subprocess
import threading
import json

import core.config as config
import ui.status as status

font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 12)
font_item  = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11)
font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 9)

AP_CON_NAME = "KeyCrowSetupAP"

# ===== Config helpers (same pattern as status_menu.py's _cfg/_set) =====
def _cfg():
    return config.load().get("wifi_setup", {})

# ===== Shared state between the HTTP server thread and the OLED loop =====
_lock = threading.Lock()
_state = {
    "phase": "idle",       # idle | scanning | list_ready | rescanning | connecting | checking | success | failed
    "networks": [],        # [{"ssid": str, "signal": int}, ...]
    "message": "",
    "ip": "",
    "ping_target": "",
    "ping_ok": False,
}

def _set_state(**kwargs):
    with _lock:
        _state.update(kwargs)

def _get_state():
    with _lock:
        return dict(_state)

# ===== nmcli helpers =====
def _run(cmd, timeout=15):
    """Best-effort run, returns stdout text or '' on any failure."""
    try:
        return subprocess.check_output(cmd, stderr=subprocess.DEVNULL, timeout=timeout).decode()
    except Exception:
        return ""

def scan_networks():
    out = _run(["nmcli", "-t", "-f", "SSID,SIGNAL", "device", "wifi", "list", "--rescan", "yes"], timeout=20)
    best = {}
    for line in out.strip().split("\n"):
        if not line:
            continue
        parts = line.rsplit(":", 1)
        if len(parts) != 2:
            continue
        ssid, signal = parts
        ssid = ssid.strip()
        if not ssid:
            continue
        try:
            signal = int(signal)
        except ValueError:
            signal = 0
        if ssid not in best or signal > best[ssid]:
            best[ssid] = signal
    networks = [{"ssid": s, "signal": sig} for s, sig in best.items()]
    networks.sort(key=lambda n: n["signal"], reverse=True)
    return networks

def start_ap():
    cfg = _cfg()
    ssid = cfg.get("ap_ssid", "KeyCrow-Setup")
    password = cfg.get("ap_password", "keycrow123")
    ip = cfg.get("portal_ip", "10.42.0.1")

    _run(["nmcli", "connection", "delete", AP_CON_NAME])  # clean slate, ignore if it doesn't exist
    _run(["nmcli", "connection", "add", "type", "wifi", "ifname", "wlan0",
          "con-name", AP_CON_NAME, "autoconnect", "no", "ssid", ssid])
    _run(["nmcli", "connection", "modify", AP_CON_NAME,
          "802-11-wireless.mode", "ap",
          "802-11-wireless.band", "bg",
          "ipv4.method", "shared",
          "ipv4.addresses", f"{ip}/24",
          "wifi-sec.key-mgmt", "wpa-psk",
          "wifi-sec.psk", password])

    try:
        proc = subprocess.run(["nmcli", "connection", "up", AP_CON_NAME],
                               capture_output=True, text=True, timeout=20)
        up_err = (proc.stderr or proc.stdout or "").strip()
    except Exception as e:
        up_err = str(e)

    # Don't trust the exit code alone -- we've already seen nmcli report
    # success (silently, no error) while the AP never actually came up
    # (e.g. the polkit permissions issue). Confirm against real state.
    state = _run(["nmcli", "-g", "GENERAL.STATE", "connection", "show", AP_CON_NAME]).strip()
    really_up = state.startswith("activated")

    if not really_up:
        print(f"[wifi_setup] AP failed to come up. nmcli said: {up_err!r} state: {state!r}")

    return really_up

def stop_ap():
    _run(["nmcli", "connection", "down", AP_CON_NAME])

def _get_ip():
    """wlan0's current IPv4 address, or '' if it doesn't have one (yet)."""
    out = _run(["nmcli", "-g", "IP4.ADDRESS", "device", "show", "wlan0"], timeout=5)
    first = out.strip().split("\n")[0] if out.strip() else ""
    return first.split("/")[0] if first else ""

def _get_gateway():
    out = _run(["nmcli", "-g", "IP4.GATEWAY", "device", "show", "wlan0"], timeout=5)
    return out.strip().split("\n")[0] if out.strip() else ""

def _ping(host, count=3, timeout=2):
    """True if host answers, False otherwise (or if there's no host to try)."""
    if not host:
        return False
    try:
        proc = subprocess.run(
            ["ping", "-c", str(count), "-W", str(timeout), host],
            capture_output=True, text=True, timeout=count * timeout + 3
        )
        return proc.returncode == 0
    except Exception:
        return False

def _rescan_worker():
    """Runs in a background thread. Briefly drops the AP to get a live
    scan, then brings it back up. The phone will disconnect from the
    setup WiFi for a few seconds during this."""
    _set_state(phase="rescanning", message="Rescanning...")
    stop_ap()
    sleep(1)
    networks = scan_networks()
    ap_ok = start_ap()
    msg = "" if ap_ok else "AP FAILED to restart - see console"
    _set_state(phase="list_ready", networks=networks, message=msg)

def _forget_saved_profile(ssid):
    """Delete any existing saved connection profile matching this SSID
    (except the AP's own profile). Without this, 'nmcli device wifi
    connect' silently reuses a pre-existing profile and IGNORES the
    password just typed into the portal -- if that old profile's stored
    secret is stale, the connect fails with no useful explanation."""
    out = _run(["nmcli", "-t", "-f", "NAME,TYPE", "connection", "show"])
    for line in out.strip().split("\n"):
        if not line:
            continue
        parts = line.rsplit(":", 1)
        if len(parts) != 2:
            continue
        name, ctype = parts
        if ctype != "802-11-wireless" or name == AP_CON_NAME:
            continue
        profile_ssid = _run(["nmcli", "-g", "802-11-wireless.ssid", "connection", "show", name]).strip()
        if profile_ssid == ssid:
            _run(["nmcli", "connection", "delete", name])

def _connect_worker(ssid, password):
    """Runs in a background thread. Tears down the AP as a side effect,
    since this hardware can only be an AP or a client at once. Result
    is shown on the device's own screen since the phone loses the portal
    connection the moment the AP goes down."""
    _set_state(phase="connecting", message=f"Connecting to {ssid}...")
    stop_ap()
    sleep(1)
    _forget_saved_profile(ssid)

    # The network list in the portal could be a minute+ old by the time the
    # user actually taps Connect -- refresh it for this specific SSID so a
    # since-expired scan cache entry (common on weaker/5GHz signals) doesn't
    # cause a bogus "no network found" failure.
    _run(["nmcli", "device", "wifi", "rescan", "ifname", "wlan0", "ssid", ssid], timeout=10)
    sleep(2)

    cmd = ["nmcli", "-w", "35", "device", "wifi", "connect", ssid]
    if password:
        cmd += ["password", password]

    err_output = ""
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
        success = proc.returncode == 0
        err_output = (proc.stderr or proc.stdout or "").strip()
    except subprocess.TimeoutExpired:
        success = False
        err_output = "nmcli timed out"
    except Exception as e:
        success = False
        err_output = str(e)

    if success:
        _set_state(phase="checking", message="Getting IP address...")

        # DHCP can take a couple seconds after association succeeds
        ip = ""
        for _ in range(6):
            ip = _get_ip()
            if ip:
                break
            sleep(1)

        gateway = _get_gateway()
        ping_target = gateway or "8.8.8.8"
        _set_state(message=f"Pinging {ping_target}...")
        ping_ok = _ping(ping_target) if ip else False

        if ip:
            msg = f"Connected to {ssid}!"
        else:
            msg = f"Joined {ssid} but no IP yet"

        _set_state(phase="success", message=msg, ip=ip, ping_target=ping_target, ping_ok=ping_ok)
    else:
        # Print the real reason to the console (visible over SSH) since
        # the OLED only has room for ~24 characters.
        print(f"[wifi_setup] connect to {ssid!r} failed: {err_output}")
        reason = err_output.replace("Error: ", "").strip() or "unknown error"
        _set_state(phase="failed", message=f"Failed: {reason[:24]}")
        sleep(2)
        ap_ok = start_ap()
        if ap_ok:
            _set_state(phase="list_ready", message="Setup AP restarted. Try again.")
        else:
            _set_state(phase="list_ready", message="AP restart FAILED - see console")

# ===== Web portal =====
PORTAL_HTML = """<!doctype html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>KeyCrow WiFi Setup</title>
<style>
body { font-family: sans-serif; background:#111; color:#eee; padding: 16px; }
h1 { font-size: 20px; }
button { padding: 10px 16px; font-size: 16px; margin: 6px 4px 6px 0; border-radius: 6px; border: none; background:#2a7; color:#fff; }
.network { padding: 10px; margin: 6px 0; background:#222; border-radius: 6px; }
.network:active { background:#333; }
input { padding: 8px; font-size: 16px; width: 100%; box-sizing: border-box; margin: 8px 0; }
#status, #note { margin-top: 12px; font-size: 14px; }
#note { color: #aaa; }
</style>
</head>
<body>
<h1>KeyCrow WiFi Setup</h1>
<button onclick="rescan()">Rescan</button>
<button onclick="loadNetworks()">Refresh List</button>
<div id="networks">Loading...</div>

<div id="passform" style="display:none;">
  <p>Enter password for <b id="chosenSsid"></b>:</p>
  <input type="password" id="pw" placeholder="Password">
  <button onclick="connect()">Connect</button>
</div>

<div id="status"></div>
<div id="note"></div>

<script>
let chosen = null;

function loadNetworks() {
  document.getElementById("networks").innerText = "Loading...";
  fetch("/networks").then(r => r.json()).then(data => {
    const el = document.getElementById("networks");
    el.innerHTML = "";
    if (data.networks.length === 0) {
      el.innerText = "No networks found. Try Rescan.";
      return;
    }
    data.networks.forEach(n => {
      const div = document.createElement("div");
      div.className = "network";
      div.innerText = n.ssid + "  (" + n.signal + "%)";
      div.onclick = () => selectNetwork(n.ssid);
      el.appendChild(div);
    });
  });
}

function rescan() {
  document.getElementById("note").innerText =
    "Rescanning \u2014 this device will briefly drop your connection to '" +
    "this WiFi for about 10 seconds. Reconnect, then tap Refresh List.";
  fetch("/rescan", { method: "POST" }).catch(() => {});
}

function selectNetwork(ssid) {
  chosen = ssid;
  document.getElementById("chosenSsid").innerText = ssid;
  document.getElementById("passform").style.display = "block";
}

function connect() {
  const pw = document.getElementById("pw").value;
  document.getElementById("status").innerText =
    "Attempting to connect... check the KeyCrow screen for the result. " +
    "This page will likely lose connection now \u2014 that's expected.";
  fetch("/connect", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({ssid: chosen, password: pw})
  }).catch(() => {});
}

window.onload = loadNetworks;
</script>
</body>
</html>
"""

class _PortalHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # keep the console quiet

    def _send_json(self, obj, code=200):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            body = PORTAL_HTML.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/networks":
            self._send_json({"networks": _get_state()["networks"]})
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/rescan":
            self._send_json({"ok": True, "message": "Rescanning"})
            threading.Thread(target=_rescan_worker, daemon=True).start()
        elif self.path == "/connect":
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length) if length else b"{}"
            try:
                data = json.loads(raw)
            except Exception:
                data = {}
            ssid = data.get("ssid", "")
            password = data.get("password", "")

            self._send_json({"ok": True, "message": "Attempting connection"})
            self.wfile.flush()

            threading.Thread(target=_connect_worker, args=(ssid, password), daemon=True).start()
        else:
            self.send_response(404)
            self.end_headers()

_httpd = None

def start_server():
    global _httpd
    port = _cfg().get("portal_port", 8080)
    _httpd = ThreadingHTTPServer(("0.0.0.0", port), _PortalHandler)
    threading.Thread(target=_httpd.serve_forever, daemon=True).start()

def stop_server():
    global _httpd
    if _httpd:
        _httpd.shutdown()
        _httpd = None

# ===== OLED screen loop, called from the WiFi Tools "Connect" item =====
def run(device, buttons):
    cfg = _cfg()
    ssid = cfg.get("ap_ssid", "KeyCrow-Setup")
    password = cfg.get("ap_password", "keycrow123")
    ip = cfg.get("portal_ip", "10.42.0.1")
    port = cfg.get("portal_port", 8080)

    def _draw_simple(line1, line2=""):
        with canvas(device) as draw:
            draw.rectangle(device.bounding_box, outline="black", fill="black")
            draw.text((4, 0), "WiFi Setup", font=font_title, fill="white")
            draw.line((0, 14, 127, 14), fill="white")
            status.draw_menu_icons(draw, y=2)
            draw.text((4, 22), line1, font=font_item, fill="white")
            if line2:
                draw.text((4, 36), line2, font=font_small, fill="white")

    # Take full manual control of wlan0 for the whole setup session. Without
    # this, the instant the AP (or any connection) drops, NetworkManager's
    # own policy immediately tries to auto-activate whatever saved profile
    # it likes best -- racing our own explicit connect commands and
    # sometimes winning, landing you on the wrong network.
    _run(["nmcli", "device", "set", "wlan0", "autoconnect", "no"])

    # Pre-scan BEFORE the AP goes up, while the radio is still free to scan
    _set_state(phase="scanning", message="Scanning nearby networks...")
    _draw_simple("Scanning nearby", "networks...")
    networks = scan_networks()
    _set_state(networks=networks)

    _draw_simple("Starting setup", "access point...")
    ap_ok = start_ap()
    start_server()
    if ap_ok:
        _set_state(phase="list_ready", message="")
    else:
        _set_state(phase="list_ready", message="AP FAILED - see console")

    try:
        while True:
            st = _get_state()

            if st["phase"] == "success":
                # Dedicated result screen — held until the user presses BACK,
                # since this is the one thing they actually need to read.
                with canvas(device) as draw:
                    draw.rectangle(device.bounding_box, outline="black", fill="black")
                    draw.text((4, 0), "WiFi Setup", font=font_title, fill="white")
                    draw.line((0, 14, 127, 14), fill="white")
                    status.draw_menu_icons(draw, y=2)

                    y = 17
                    draw.text((4, y), st["message"][:24], font=font_item, fill="white"); y += 13
                    draw.text((4, y), f"IP: {st['ip'] or '(none yet)'}", font=font_small, fill="white"); y += 11
                    ping_label = "OK" if st["ping_ok"] else "FAILED"
                    draw.text((4, y), f"Ping {st['ping_target']}: {ping_label}", font=font_small, fill="white"); y += 11
                    draw.text((4, y), "BACK to exit", font=font_small, fill="white")

                if buttons.is_pressed("BACK"):
                    sleep(0.2)
                    break

                sleep(0.2)
                continue

            with canvas(device) as draw:
                draw.rectangle(device.bounding_box, outline="black", fill="black")
                draw.text((4, 0), "WiFi Setup", font=font_title, fill="white")
                draw.line((0, 14, 127, 14), fill="white")
                status.draw_menu_icons(draw, y=2)

                y = 17
                draw.text((4, y), f"Join: {ssid}", font=font_small, fill="white"); y += 11
                draw.text((4, y), f"Pass: {password}", font=font_small, fill="white"); y += 11
                draw.text((4, y), f"Visit: {ip}:{port}", font=font_small, fill="white"); y += 11

                if st["message"]:
                    draw.text((4, y), st["message"][:24], font=font_small, fill="white")

            if buttons.is_pressed("BACK"):
                sleep(0.2)
                break

            sleep(0.2)
    finally:
        stop_server()
        stop_ap()
        # Hand control of wlan0 back to NetworkManager's normal policy --
        # e.g. so it reconnects on its own after a reboot.
        _run(["nmcli", "device", "set", "wlan0", "autoconnect", "yes"])
