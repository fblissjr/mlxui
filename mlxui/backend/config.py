"""
Configuration module for mlxui backend.
Loads settings from a JSON file, providing defaults if the file doesn't exist.
"""
import os
import json
import logging
import copy
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, List

logger = logging.getLogger("mlxui.backend.config")

CONFIG_ENV_VAR = "MLXUI_CONFIG_DIR"
if CONFIG_ENV_VAR in os.environ:
    DEFAULT_CONFIG_DIR = Path(os.environ[CONFIG_ENV_VAR]).expanduser().resolve()
elif "XDG_CONFIG_HOME" in os.environ:
    DEFAULT_CONFIG_DIR = Path(os.environ["XDG_CONFIG_HOME"]).expanduser().resolve() / "mlxui"
else:
    DEFAULT_CONFIG_DIR = Path.home() / ".config" / "mlxui"

try:
    DEFAULT_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
except OSError:
    logger.warning(f"Could not create primary config directory at {DEFAULT_CONFIG_DIR}, falling back to ~/.mlxui")
    DEFAULT_CONFIG_DIR = Path.home() / ".mlxui"
    try:
        DEFAULT_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    except OSError as e_fallback:
        logger.error(f"Could not create fallback config directory at {DEFAULT_CONFIG_DIR}: {e_fallback}. Using in-memory defaults only.")

DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "config.json"
DEFAULT_MODELS_SCAN_DIR = DEFAULT_CONFIG_DIR / "models"
DEFAULT_KV_CACHE_DIR = DEFAULT_CONFIG_DIR / "_kv_caches"

DEFAULT_CONFIG = {
    "app": {
        "host": "127.0.0.1",
        "port": 8000,
        "reload_backend_on_change": False,
    },
    "models": {
        "scan_directories": [str(DEFAULT_MODELS_SCAN_DIR)],
        "default_model_identifier": None, # e.g., "mlx-community/abc-model"
        "cache_directory": str(DEFAULT_KV_CACHE_DIR),
    },
    "generation": {
        "default_max_tokens": 512,
        "default_temp": 0.6,
        "default_top_p": 0.9,
        "default_top_k": 50,
        "default_repetition_penalty": 1.1,
        "default_repetition_context_size": 25,
        "default_seed": -1, # -1 for random
    },
    "performance": {
        "enabled": True,
        "history_size": 120, # Number of data points for charts
        "update_interval_ms": 2000, # How often backend pushes perf updates
    }
}

class Config:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._config_dir = DEFAULT_CONFIG_DIR
        self._config_file = DEFAULT_CONFIG_FILE
        self._config = copy.deepcopy(DEFAULT_CONFIG)
        self._ensure_directories()
        self.load()
        self._initialized = True

    def _ensure_directories(self):
        try:
            self._config_dir.mkdir(parents=True, exist_ok=True)
            for scan_dir_str in self.get("models.scan_directories", []):
                 scan_dir = Path(scan_dir_str).expanduser().resolve()
                 if scan_dir == DEFAULT_MODELS_SCAN_DIR: # Only auto-create the default models dir
                     scan_dir.mkdir(parents=True, exist_ok=True)
                     break
            kv_cache_dir_str = self.get("models.cache_directory", str(DEFAULT_KV_CACHE_DIR))
            kv_cache_dir = Path(kv_cache_dir_str).expanduser().resolve()
            kv_cache_dir.mkdir(parents=True, exist_ok=True)

        except OSError as e:
            logger.warning(f"Could not create necessary config/model directories: {e}")

    def load(self) -> None:
        if self._config_file.exists() and self._config_file.is_file():
            try:
                with open(self._config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                self._deep_update(self._config, loaded_config)
                logger.info(f"Loaded configuration from {self._config_file}")
            except json.JSONDecodeError as e:
                logger.error(f"Error decoding JSON from {self._config_file}: {e}. Using defaults and attempting to save.")
                self._config = copy.deepcopy(DEFAULT_CONFIG)
                self.save()
            except Exception as e:
                logger.error(f"Could not load configuration from {self._config_file}: {e}. Using defaults.")
                self._config = copy.deepcopy(DEFAULT_CONFIG)
        else:
            logger.info(f"Configuration file not found at {self._config_file}. Using default settings and creating file.")
            self.save()

    def save(self) -> bool:
        try:
            self._config_dir.mkdir(parents=True, exist_ok=True)
            sorted_config = self._sort_dict(self._config)
            with open(self._config_file, 'w', encoding='utf-8') as f:
                json.dump(sorted_config, f, indent=2, ensure_ascii=False)
                f.write('\n')
            logger.debug(f"Configuration saved to {self._config_file}")
            return True
        except OSError as e:
            logger.error(f"Could not write configuration file {self._config_file}: {e}")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
        return False

    def get(self, key: Optional[str] = None, default: Any = None) -> Any:
        if key is None:
            return self._config
        keys = key.split('.')
        value = self._config
        try:
            for k in keys:
                if isinstance(value, dict):
                    value = value[k]
                else:
                    raise KeyError(f"Intermediate key '{k}' is not a dictionary in path '{key}'.")
            return value
        except KeyError:
            logger.debug(f"Configuration key '{key}' not found, returning default: {default}")
            return default
        except Exception as e:
             logger.error(f"Unexpected error getting config key '{key}': {e}")
             return default

    def set(self, key: str, value: Any) -> bool:
        keys = key.split('.')
        config_ref = self._config
        try:
            for k_idx, k in enumerate(keys[:-1]):
                config_ref = config_ref.setdefault(k, {})
                if not isinstance(config_ref, dict):
                    logger.error(f"Cannot set nested key '{key}': Intermediate key '{k}' (index {k_idx}) is not a dictionary.")
                    return False
            target_key = keys[-1]
            config_ref[target_key] = value
            logger.info(f"Configuration updated: '{key}' set to '{value}'.")
            return self.save()
        except Exception as e:
            logger.error(f"Error setting configuration key '{key}': {e}")
            return False

    def _deep_update(self, target: Dict[str, Any], source: Dict[str, Any]):
        for key, value in source.items():
            if isinstance(value, dict) and isinstance(target.get(key), dict):
                self._deep_update(target[key], value)
            else:
                target[key] = value

    def _sort_dict(self, d: Dict) -> Dict:
        return {k: (self._sort_dict(v) if isinstance(v, dict) else v)
                for k, v in sorted(d.items())}

config = Config()