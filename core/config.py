import toml
from pathlib import Path

CONFIG_PATH = Path.home() / "keycrow" / "config.toml"

def load():
    if not CONFIG_PATH.exists():
        default = {
            "splash": {"current": "default"},
            "ui": {}
        }
        save(default)
        return default
    return toml.load(CONFIG_PATH)

def save(data):
    with open(CONFIG_PATH, "w") as f:
        toml.dump(data, f)

def get_splash():
    cfg = load()
    return cfg.get("splash", {}).get("current", "default")

def set_splash(name: str):
    cfg = load()
    if "splash" not in cfg:
        cfg["splash"] = {}
    cfg["splash"]["current"] = name
    save(cfg)

def get_status_dict():
    """Return the whole 'status' config section (status bar icon settings)."""
    cfg = load()
    return cfg.get("status", {})

def set_status(key: str, value):
    cfg = load()
    if "status" not in cfg:
        cfg["status"] = {}
    cfg["status"][key] = value
    save(cfg)
