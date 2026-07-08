import os
from dataclasses import dataclass
from typing import Any, Optional, Tuple

import yaml
from yaml import YAMLError

from other.eutils import time_utils as time


@dataclass
class LoggerConfig:
    time_format: str = "[%H:%M:%S]"
    default_user: str = "System"
    log_file: str = "log.log"
    include_timestamp: bool = True
    include_level: bool = True
    separator: str = " | "
    file_mode: str = "a"
    write_to_console: bool = False
    auto_create_dirs: bool = True
    enabled_levels: Tuple[str, ...] = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")


def _to_bool(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"1", "true", "yes", "on"}:
            return True
        if lowered in {"0", "false", "no", "off"}:
            return False
    return default


def _to_levels(value: Any) -> Tuple[str, ...]:
    defaults = LoggerConfig().enabled_levels
    if isinstance(value, str):
        raw = [part.strip() for part in value.split(",")]
        levels = [part.upper() for part in raw if part]
        return tuple(levels) if levels else defaults
    if isinstance(value, (list, tuple, set)):
        levels = [str(item).strip().upper() for item in value if str(item).strip()]
        return tuple(levels) if levels else defaults
    return defaults


def _find_config_path() -> Optional[str]:
    if os.path.exists("config.yml"):
        return "config.yml"
    if os.path.exists("config.yaml"):
        return "config.yaml"
    return None


def _normalize_config(raw: dict[str, Any]) -> dict[str, Any]:
    defaults = LoggerConfig()
    mode = str(raw.get("file_mode", defaults.file_mode)).lower()
    if mode not in {"a", "w"}:
        mode = defaults.file_mode

    return {
        "time_format": str(raw.get("time_format", defaults.time_format)),
        "default_user": str(raw.get("default_user", defaults.default_user)),
        "log_file": str(raw.get("log_file", defaults.log_file)),
        "include_timestamp": _to_bool(raw.get("include_timestamp", defaults.include_timestamp), defaults.include_timestamp),
        "include_level": _to_bool(raw.get("include_level", defaults.include_level), defaults.include_level),
        "separator": str(raw.get("separator", defaults.separator)),
        "file_mode": mode,
        "write_to_console": _to_bool(raw.get("write_to_console", defaults.write_to_console), defaults.write_to_console),
        "auto_create_dirs": _to_bool(raw.get("auto_create_dirs", defaults.auto_create_dirs), defaults.auto_create_dirs),
        "enabled_levels": _to_levels(raw.get("enabled_levels", defaults.enabled_levels)),
    }


def _apply_env_overrides(config: dict[str, Any], env_prefix: str) -> dict[str, Any]:
    mapping = {
        "TIME_FORMAT": "time_format",
        "DEFAULT_USER": "default_user",
        "LOG_FILE": "log_file",
        "INCLUDE_TIMESTAMP": "include_timestamp",
        "INCLUDE_LEVEL": "include_level",
        "SEPARATOR": "separator",
        "FILE_MODE": "file_mode",
        "WRITE_TO_CONSOLE": "write_to_console",
        "AUTO_CREATE_DIRS": "auto_create_dirs",
        "ENABLED_LEVELS": "enabled_levels",
    }

    merged = dict(config)
    for env_key, config_key in mapping.items():
        full_key = f"{env_prefix}{env_key}"
        if full_key in os.environ:
            merged[config_key] = os.environ[full_key]

    return _normalize_config(merged)


def get_config(config_path: Optional[str] = None, env_prefix: str = "EUTILS_LOGGER_") -> dict[str, Any]:
    path = config_path or _find_config_path()
    loaded: dict[str, Any] = {}

    if path and os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                parsed = yaml.safe_load(f) or {}
            if isinstance(parsed, dict):
                loaded = parsed
        except (OSError, YAMLError):
            loaded = {}

    config = _normalize_config(loaded)
    return _apply_env_overrides(config, env_prefix=env_prefix)


def save_config(config: dict[str, Any], config_path: str = "config.yml") -> str:
    normalized = _normalize_config(config)
    payload = dict(normalized)
    payload["enabled_levels"] = list(normalized["enabled_levels"])

    parent = os.path.dirname(config_path)
    if parent:
        os.makedirs(parent, exist_ok=True)

    with open(config_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(payload, f, sort_keys=False)

    return config_path


def update_config(updates: dict[str, Any], config_path: str = "config.yml") -> dict[str, Any]:
    current = get_config(config_path=config_path)
    merged = dict(current)
    merged.update(updates)
    save_config(merged, config_path=config_path)
    return get_config(config_path=config_path)


def clear_log(log_file: Optional[str] = None, config_path: Optional[str] = None) -> bool:
    cfg = get_config(config_path=config_path)
    target = str(log_file or cfg["log_file"])
    if os.path.exists(target):
        os.remove(target)
        return True
    return False


class Logger:
    def __init__(
        self,
        config: Optional[dict[str, Any]] = None,
        config_path: Optional[str] = None,
        env_prefix: str = "EUTILS_LOGGER_",
    ):
        self.config_path = config_path
        self.env_prefix = env_prefix
        self.config = _normalize_config(config) if config else get_config(config_path=config_path, env_prefix=env_prefix)

    @property
    def log_file(self) -> str:
        return str(self.config.get("log_file", "log.log"))

    @property
    def time_format(self) -> str:
        return str(self.config.get("time_format", "[%H:%M:%S]"))

    @property
    def default_user(self) -> str:
        return str(self.config.get("default_user", "System"))

    @property
    def separator(self) -> str:
        return str(self.config.get("separator", " | "))

    @property
    def include_timestamp(self) -> bool:
        return bool(self.config.get("include_timestamp", True))

    @property
    def include_level(self) -> bool:
        return bool(self.config.get("include_level", True))

    @property
    def file_mode(self) -> str:
        mode = str(self.config.get("file_mode", "a")).lower()
        return "w" if mode == "w" else "a"

    @property
    def write_to_console(self) -> bool:
        return bool(self.config.get("write_to_console", False))

    @property
    def auto_create_dirs(self) -> bool:
        return bool(self.config.get("auto_create_dirs", True))

    @property
    def enabled_levels(self) -> Tuple[str, ...]:
        return _to_levels(self.config.get("enabled_levels", LoggerConfig().enabled_levels))

    def reload_config(self) -> dict[str, Any]:
        self.config = get_config(config_path=self.config_path, env_prefix=self.env_prefix)
        return dict(self.config)

    def set_config(self, updates: dict[str, Any], persist: bool = False) -> dict[str, Any]:
        merged = dict(self.config)
        merged.update(updates)
        self.config = _normalize_config(merged)

        if persist:
            target = self.config_path or _find_config_path() or "config.yml"
            save_config(self.config, config_path=target)

        return dict(self.config)

    def _should_log_level(self, level: str) -> bool:
        return level.upper() in self.enabled_levels

    def _format_line(self, message: Any, user: str, level: str) -> str:
        pieces: list[str] = []
        if self.include_timestamp:
            pieces.append(time.format_datetime(fmt=self.time_format))
        if self.include_level:
            pieces.append(level)
        pieces.append(user)

        prefix = self.separator.join(pieces)
        return f"{prefix}: {message}\n"

    def write(
        self,
        message: Any,
        user: Optional[str] = None,
        level: str = "INFO",
        console: Optional[bool] = None,
    ) -> str:
        level_name = str(level).upper()
        if not self._should_log_level(level_name):
            return ""

        who = str(user or self.default_user)
        line = self._format_line(message=message, user=who, level=level_name)

        parent = os.path.dirname(self.log_file)
        if parent and self.auto_create_dirs:
            os.makedirs(parent, exist_ok=True)

        with open(self.log_file, self.file_mode, encoding="utf-8") as f:
            f.write(line)

        use_console = self.write_to_console if console is None else bool(console)
        if use_console:
            print(line, end="")

        return line

    def debug(self, message: Any, user: Optional[str] = None, console: Optional[bool] = None) -> str:
        return self.write(message=message, user=user, level="DEBUG", console=console)

    def info(self, message: Any, user: Optional[str] = None, console: Optional[bool] = None) -> str:
        return self.write(message=message, user=user, level="INFO", console=console)

    def warning(self, message: Any, user: Optional[str] = None, console: Optional[bool] = None) -> str:
        return self.write(message=message, user=user, level="WARNING", console=console)

    def error(self, message: Any, user: Optional[str] = None, console: Optional[bool] = None) -> str:
        return self.write(message=message, user=user, level="ERROR", console=console)

    def critical(self, message: Any, user: Optional[str] = None, console: Optional[bool] = None) -> str:
        return self.write(message=message, user=user, level="CRITICAL", console=console)


def log_message(
    message: Any,
    user: Optional[str] = None,
    level: str = "INFO",
    config_path: Optional[str] = None,
) -> str:
    return Logger(config_path=config_path).write(message=message, user=user, level=level)


class log:
    # Backward-compatible API: log("hello")
    def __init__(self, what_to_log: Any, user: Optional[str] = None):
        self.line = log_message(what_to_log, user=user)

    def _log(self, log_text: Any, user: Optional[str] = None) -> str:
        self.line = log_message(log_text, user=user)
        return self.line
