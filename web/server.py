"""KeyCrow web UI — http://keycrow.local:8080"""
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from flask import Flask, jsonify, render_template, request

import core.config as config
from apps.music.player import (
    Player,
    MUSIC_DIR,
    list_library,
    list_paired_devices,
    set_output,
    get_volume,
    set_volume,
    BluetoothConnector,
)
import ui.status as status

app = Flask(__name__)
player = Player()
_tracks = []
_connector = None
_play_lock = threading.Lock()


def _music_cfg():
    return config.load().get("music", {})


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/status")
def api_status():
    st = status.get_status()
    cfg = _music_cfg()
    return jsonify({
        "battery": st.get("battery"),
        "charging": st.get("charging"),
        "wifi": st.get("wifi"),
        "bluetooth": st.get("bluetooth"),
        "volume": get_volume(),
        "output": cfg.get("output", "auto"),
        "track": player.current_track(),
        "paused": player.is_paused(),
        "playing": player.current_track() is not None and not player.finished(),
        "music_dir": str(MUSIC_DIR),
    })


@app.route("/api/volume", methods=["POST"])
def api_volume():
    data = request.get_json(force=True, silent=True) or {}
    if "percent" in data:
        v = set_volume(int(data["percent"]))
    elif data.get("delta") is not None:
        v = set_volume(get_volume() + int(data["delta"]))
    else:
        return jsonify({"ok": False, "error": "need percent or delta"}), 400
    return jsonify({"ok": True, "volume": v})


@app.route("/api/output", methods=["POST"])
def api_output():
    data = request.get_json(force=True, silent=True) or {}
    mode = data.get("mode", "aux")
    if mode not in ("auto", "aux", "bluetooth"):
        return jsonify({"ok": False, "error": "bad mode"}), 400
    cfg = config.load()
    cfg.setdefault("music", {})
    cfg["music"]["output"] = mode
    config.save(cfg)
    if mode in ("aux", "auto"):
        set_output(mode)
    return jsonify({"ok": True, "output": mode})


@app.route("/api/library")
def api_library():
    rel = request.args.get("path", "") or ""
    try:
        folder = MUSIC_DIR / rel if rel else MUSIC_DIR
        if not folder.exists():
            folder.mkdir(parents=True, exist_ok=True)
        items = list_library(rel)
        return jsonify({
            "path": rel,
            "items": items,
            "music_dir": str(MUSIC_DIR),
            "count": len(items),
        })
    except Exception as e:
        return jsonify({
            "path": rel,
            "items": [],
            "error": str(e),
            "music_dir": str(MUSIC_DIR),
            "count": 0,
        }), 500


@app.route("/api/play", methods=["POST"])
def api_play():
    global _tracks
    data = request.get_json(force=True, silent=True) or {}
    rel = data.get("path") or data.get("rel")
    if not rel:
        return jsonify({"ok": False, "error": "need path"}), 400
    with _play_lock:
        player.stop()
        cfg = _music_cfg()
        mode = cfg.get("output", "auto")
        if mode in ("aux", "auto"):
            set_output(mode)
        ok = player.play(rel)
        parent = str(Path(rel).parent)
        if parent == ".":
            parent = ""
        _tracks = [i["rel"] for i in list_library(parent) if not i["is_dir"]]
    return jsonify({"ok": ok, "track": player.current_track()})


@app.route("/api/player", methods=["POST"])
def api_player():
    data = request.get_json(force=True, silent=True) or {}
    action = data.get("action")
    with _play_lock:
        if action == "pause":
            player.toggle_pause()
        elif action == "stop":
            player.stop()
        elif action == "next" and _tracks:
            cur = player.current_track()
            idx = 0
            for i, rel in enumerate(_tracks):
                if Path(rel).name == cur:
                    idx = i
                    break
            idx = (idx + 1) % len(_tracks)
            player.stop()
            player.play(_tracks[idx])
        elif action == "prev" and _tracks:
            cur = player.current_track()
            idx = 0
            for i, rel in enumerate(_tracks):
                if Path(rel).name == cur:
                    idx = i
                    break
            idx = (idx - 1) % len(_tracks)
            player.stop()
            player.play(_tracks[idx])
        else:
            return jsonify({"ok": False, "error": "bad action"}), 400
    return jsonify({
        "ok": True,
        "track": player.current_track(),
        "paused": player.is_paused(),
    })


@app.route("/api/bt/paired")
def api_bt_paired():
    try:
        devices = [{"mac": m, "name": n} for m, n in list_paired_devices()]
        return jsonify({"devices": devices, "count": len(devices)})
    except Exception as e:
        return jsonify({"devices": [], "count": 0, "error": str(e)}), 500


@app.route("/api/bt/connect", methods=["POST"])
def api_bt_connect():
    global _connector
    data = request.get_json(force=True, silent=True) or {}
    mac = data.get("mac")
    if not mac:
        return jsonify({"ok": False, "error": "need mac"}), 400
    _connector = BluetoothConnector()
    _connector.start(mac)
    return jsonify({"ok": True, "started": True})


@app.route("/api/bt/connect/status")
def api_bt_connect_status():
    if _connector is None:
        return jsonify({"done": True, "success": False})
    return jsonify({
        "done": _connector.done,
        "success": _connector.success,
        "audio_ok": _connector.audio_ok,
        "needs_confirm": _connector.needs_confirm,
        "passkey": _connector.passkey,
    })


if __name__ == "__main__":
    print(f"[keycrow-web] MUSIC_DIR={MUSIC_DIR}")
    app.run(host="0.0.0.0", port=8080, debug=False)
