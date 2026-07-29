import toml
from pathlib import Path

CONFIG_PATH = Path.home() / "keycrow" / "config.toml"

def load():
    if not CONFIG_PATH.exists():
        # Create default if missing
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
