import os
import yaml
from pathlib import Path
from typing import Any, Dict

class Config:
    _instance = None
    _config: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self):
        """Load configuration from yaml and environment variables"""
        # Determine config path (default to config.yaml in project root)
        root_dir = Path(__file__).parent.parent
        config_path = root_dir / "config.yaml"
        
        if config_path.exists():
            with open(config_path, "r") as f:
                self._config = yaml.safe_load(f)
        else:
            # Fallback or empty config if file missing
            self._config = {}

        # Override with environment variables where necessary
        self._apply_env_overrides()

    def _apply_env_overrides(self):
        """Apply environment variable overrides"""
        # OpenAI API Key
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            if "api" not in self._config:
                self._config["api"] = {}
            if "openai" not in self._config["api"]:
                self._config["api"]["openai"] = {}
            self._config["api"]["openai"]["api_key"] = api_key

        # OpenAI Model
        model = os.getenv("OPENAI_MODEL")
        if model:
             if "api" not in self._config:
                self._config["api"] = {}
             if "openai" not in self._config["api"]:
                self._config["api"]["openai"] = {}
             self._config["api"]["openai"]["model"] = model
             
        # MT5 API URL
        mt5_url = os.getenv("MT5_API_URL")
        if mt5_url:
            if "trading" not in self._config:
                self._config["trading"] = {}
            if "mt5" not in self._config["trading"]:
                self._config["trading"]["mt5"] = {}
            self._config["trading"]["mt5"]["api_url"] = mt5_url

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value using dot notation (e.g., 'api.openai.model')"""
        keys = key.split(".")
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

# Global config instance
config = Config()
