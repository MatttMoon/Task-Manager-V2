# core/config.py
import json, os, copy

CONFIG_FILE = "app_settings.json"

GLOBAL_DEFAULTS = {
    "theme": "aurora",
    "accent": "#7AA2F7",
    "users": {}
}

USER_DEFAULTS = {
    "groups": [],
    "task_groups": {},
    "priorities": {},
    "completion_log": [],
    "reminded": {}
}

def load_cfg():
    """Load global config from JSON file (or create with defaults)."""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f) or {}
                for k, v in GLOBAL_DEFAULTS.items():
                    if k == "users":
                        data.setdefault("users", {})
                    else:
                        data.setdefault(k, v)
                return data
    except Exception:
        pass
    save_cfg(GLOBAL_DEFAULTS)
    return copy.deepcopy(GLOBAL_DEFAULTS)

def save_cfg(cfg: dict):
    """Save config safely back to JSON file."""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    except Exception as e:
        print("Error saving config:", e)

def user_bucket(cfg: dict, user_id: int) -> dict:
    """Make sure each user has their own section in the config."""
    ukey = str(user_id)
    cfg.setdefault("users", {})
    if ukey not in cfg["users"]:
        cfg["users"][ukey] = copy.deepcopy(USER_DEFAULTS)
        save_cfg(cfg)
    else:
        for k, v in USER_DEFAULTS.items():
            cfg["users"][ukey].setdefault(k, copy.deepcopy(v))
    return cfg["users"][ukey]

