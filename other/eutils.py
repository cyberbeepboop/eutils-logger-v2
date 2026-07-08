import os
import time
import random
import datetime
import json
import subprocess
import shutil
import hashlib
import base64
from typing import Any, Callable, Iterable, Optional, Union


class errors:
    class unusable_path(Exception):
        def __init__(self):
            super().__init__("That path does not look valid.")

    class idk_what_happened(Exception):
        def __init__(self):
            super().__init__("Something went wrong, but I do not know why yet.")

    class path_missing(Exception):
        def __init__(self):
            super().__init__("Please give me a path. The path is missing.")

    class path_not_found(Exception):
        def __init__(self, path: str):
            super().__init__(f"I could not find this path: {path}")

    class file_not_found(Exception):
        def __init__(self, path: str):
            super().__init__(f"I could not find this file: {path}")

    class folder_not_found(Exception):
        def __init__(self, path: str):
            super().__init__(f"I could not find this folder: {path}")

    class invalid_chunk_size(Exception):
        def __init__(self):
            super().__init__("Chunk size must be greater than 0.")

    class invalid_retry_attempts(Exception):
        def __init__(self):
            super().__init__("Retry attempts must be greater than 0.")

    class invalid_range(Exception):
        def __init__(self):
            super().__init__("Invalid range. Start must be less than or equal to end.")

    class empty_choices(Exception):
        def __init__(self):
            super().__init__("Choices list is empty. Please pass at least one item.")

    class invalid_file_usage(Exception):
        def __init__(self):
            super().__init__(
                "Invalid file call. Use file('name.txt') or file.exists('name.txt')."
            )

    class invalid_folder_usage(Exception):
        def __init__(self):
            super().__init__(
                "Invalid folder call. Use folder('my_dir') or folder.exists('my_dir')."
            )


def _coerce_path(path: Union[str, os.PathLike, int, float, None]) -> str:
    if path is None:
        raise errors.path_missing()

    if isinstance(path, (int, float)):
        value = str(path)
    else:
        value = os.fspath(path)

    if not str(value).strip():
        raise errors.unusable_path()

    return str(value)


class file:
    def __init__(self, path: Union[str, os.PathLike, None] = None, create: bool = True):
        self.path = _coerce_path(path)
        if create:
            self._create()

    def _create(self) -> bool:
        parent = os.path.dirname(self.path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(self.path, "a", encoding="utf-8"):
            return True

    @staticmethod
    def _path_from_target(target: Any) -> str:
        if isinstance(target, file):
            return target.path
        try:
            return _coerce_path(target)
        except Exception as ex:
            raise errors.invalid_file_usage() from ex

    def delete(self) -> bool:
        path = file._path_from_target(self)
        if os.path.exists(path):
            os.remove(path)
            return True
        return False

    def write(self, data: Any) -> bool:
        path = file._path_from_target(self)
        with open(path, "w", encoding="utf-8") as f:
            f.write(str(data))
        return True

    def read(self) -> str:
        path = file._path_from_target(self)
        if not file.exists(path):
            raise errors.file_not_found(path)
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def append(self, data: Any) -> bool:
        path = file._path_from_target(self)
        with open(path, "a", encoding="utf-8") as f:
            f.write(str(data))
        return True

    def exists(self) -> bool:
        path = file._path_from_target(self)
        return os.path.exists(path)

    def rename(self, new_path: Union[str, os.PathLike]) -> bool:
        old_path = file._path_from_target(self)
        if not file.exists(old_path):
            raise errors.path_not_found(old_path)
        new_path_str = _coerce_path(new_path)
        os.rename(old_path, new_path_str)
        if isinstance(self, file):
            self.path = new_path_str
        return True

    def size(self) -> int:
        path = file._path_from_target(self)
        if not file.exists(path):
            return 0
        return os.path.getsize(path)


class folder:
    def __init__(self, path: Union[str, os.PathLike, None] = None, create: bool = True):
        self.path = _coerce_path(path)
        if create:
            self._create()

    def _create(self) -> bool:
        os.makedirs(self.path, exist_ok=True)
        return True

    @staticmethod
    def _path_from_target(target: Any) -> str:
        if isinstance(target, folder):
            return target.path
        try:
            return _coerce_path(target)
        except Exception as ex:
            raise errors.invalid_folder_usage() from ex

    def delete(self) -> bool:
        path = folder._path_from_target(self)
        if os.path.exists(path):
            shutil.rmtree(path)
            return True
        return False

    def exists(self) -> bool:
        path = folder._path_from_target(self)
        return os.path.exists(path)

    def rename(self, new_path: Union[str, os.PathLike]) -> bool:
        old_path = folder._path_from_target(self)
        if not folder.exists(old_path):
            raise errors.folder_not_found(old_path)
        new_path_str = _coerce_path(new_path)
        os.rename(old_path, new_path_str)
        if isinstance(self, folder):
            self.path = new_path_str
        return True

    def list(self) -> list[str]:
        path = folder._path_from_target(self)
        if not folder.exists(path):
            return []
        return os.listdir(path)

    def join(self, *parts: str) -> str:
        return os.path.join(self.path, *parts)


class time_utils:
    @staticmethod
    def now_iso() -> str:
        return datetime.datetime.now().isoformat()

    @staticmethod
    def unix_time() -> int:
        return int(time.time())

    @staticmethod
    def unix_time_ms() -> int:
        return int(time.time() * 1000)

    @staticmethod
    def now_utc_iso() -> str:
        return datetime.datetime.now(datetime.UTC).isoformat()

    @staticmethod
    def timestamp_to_iso(timestamp: Union[int, float], use_utc: bool = False) -> str:
        if use_utc:
            return datetime.datetime.fromtimestamp(timestamp, datetime.UTC).isoformat()
        return datetime.datetime.fromtimestamp(timestamp).isoformat()

    @staticmethod
    def iso_to_timestamp(iso_text: str) -> float:
        return datetime.datetime.fromisoformat(iso_text).timestamp()

    @staticmethod
    def format_datetime(
        dt: Optional[datetime.datetime] = None,
        fmt: str = "%Y-%m-%d %H:%M:%S",
    ) -> str:
        value = dt or datetime.datetime.now()
        return value.strftime(fmt)

    @staticmethod
    def parse_datetime(text: str, fmt: str = "%Y-%m-%d %H:%M:%S") -> datetime.datetime:
        return datetime.datetime.strptime(text, fmt)

    @staticmethod
    def seconds_since(start_timestamp: Union[int, float]) -> float:
        return time.time() - float(start_timestamp)

    @staticmethod
    def elapsed_ms(start_timestamp: Union[int, float]) -> int:
        return int((time.time() - float(start_timestamp)) * 1000)

    @staticmethod
    def sleep_ms(milliseconds: Union[int, float]) -> None:
        if milliseconds <= 0:
            return
        time.sleep(float(milliseconds) / 1000.0)


class random_utils:
    @staticmethod
    def random_string(length: int = 12, alphabet: Optional[str] = None) -> str:
        if length <= 0:
            return ""
        chars = alphabet or "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        return "".join(random.choice(chars) for _ in range(length))

    @staticmethod
    def random_int(start: int = 0, end: int = 100) -> int:
        if start > end:
            raise errors.invalid_range()
        return random.randint(start, end)

    @staticmethod
    def random_float(
        start: float = 0.0,
        end: float = 1.0,
        decimals: Optional[int] = None,
    ) -> float:
        if start > end:
            raise errors.invalid_range()
        value = random.uniform(start, end)
        if decimals is None:
            return value
        return round(value, decimals)

    @staticmethod
    def random_bool(true_chance: float = 0.5) -> bool:
        chance = max(0.0, min(1.0, true_chance))
        return random.random() < chance

    @staticmethod
    def random_choice(items: Iterable[Any]) -> Any:
        choices = list(items)
        if not choices:
            raise errors.empty_choices()
        return random.choice(choices)

    @staticmethod
    def random_choices(items: Iterable[Any], count: int = 1, unique: bool = False) -> list[Any]:
        choices = list(items)
        if not choices:
            raise errors.empty_choices()
        if count <= 0:
            return []
        if unique:
            if count >= len(choices):
                return random.sample(choices, len(choices))
            return random.sample(choices, count)
        return random.choices(choices, k=count)

    @staticmethod
    def shuffled(items: Iterable[Any]) -> list[Any]:
        data = list(items)
        random.shuffle(data)
        return data

    @staticmethod
    def random_hex(length: int = 16) -> str:
        if length <= 0:
            return ""
        return "".join(random.choice("0123456789abcdef") for _ in range(length))

    @staticmethod
    def uuid4_text() -> str:
        import uuid

        return str(uuid.uuid4())


# Backward-compatible function aliases.
def now_iso() -> str:
    return time_utils.now_iso()


def unix_time() -> int:
    return time_utils.unix_time()


def unix_time_ms() -> int:
    return time_utils.unix_time_ms()


def now_utc_iso() -> str:
    return time_utils.now_utc_iso()


def timestamp_to_iso(timestamp: Union[int, float], use_utc: bool = False) -> str:
    return time_utils.timestamp_to_iso(timestamp, use_utc=use_utc)


def iso_to_timestamp(iso_text: str) -> float:
    return time_utils.iso_to_timestamp(iso_text)


def format_datetime(
    dt: Optional[datetime.datetime] = None,
    fmt: str = "%Y-%m-%d %H:%M:%S",
) -> str:
    return time_utils.format_datetime(dt=dt, fmt=fmt)


def parse_datetime(text: str, fmt: str = "%Y-%m-%d %H:%M:%S") -> datetime.datetime:
    return time_utils.parse_datetime(text=text, fmt=fmt)


def seconds_since(start_timestamp: Union[int, float]) -> float:
    return time_utils.seconds_since(start_timestamp)


def elapsed_ms(start_timestamp: Union[int, float]) -> int:
    return time_utils.elapsed_ms(start_timestamp)


def sleep_ms(milliseconds: Union[int, float]) -> None:
    return time_utils.sleep_ms(milliseconds)


def random_string(length: int = 12, alphabet: Optional[str] = None) -> str:
    return random_utils.random_string(length=length, alphabet=alphabet)


def random_int(start: int = 0, end: int = 100) -> int:
    return random_utils.random_int(start=start, end=end)


def random_float(start: float = 0.0, end: float = 1.0, decimals: Optional[int] = None) -> float:
    return random_utils.random_float(start=start, end=end, decimals=decimals)


def random_bool(true_chance: float = 0.5) -> bool:
    return random_utils.random_bool(true_chance=true_chance)


def random_choice(items: Iterable[Any]) -> Any:
    return random_utils.random_choice(items)


def random_choices(items: Iterable[Any], count: int = 1, unique: bool = False) -> list[Any]:
    return random_utils.random_choices(items=items, count=count, unique=unique)


def shuffled(items: Iterable[Any]) -> list[Any]:
    return random_utils.shuffled(items)


def random_hex(length: int = 16) -> str:
    return random_utils.random_hex(length=length)


def uuid4_text() -> str:
    return random_utils.uuid4_text()


def json_read(path: Union[str, os.PathLike], default: Any = None) -> Any:
    path_str = _coerce_path(path)
    if not os.path.exists(path_str):
        return default
    with open(path_str, "r", encoding="utf-8") as f:
        return json.load(f)


def json_write(path: Union[str, os.PathLike], data: Any, indent: int = 2) -> bool:
    path_str = _coerce_path(path)
    parent = os.path.dirname(path_str)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path_str, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent)
    return True


def hash_text(text: Any, algorithm: str = "sha256") -> str:
    h = hashlib.new(algorithm)
    h.update(str(text).encode("utf-8"))
    return h.hexdigest()


def b64_encode(text: Any) -> str:
    return base64.b64encode(str(text).encode("utf-8")).decode("utf-8")


def b64_decode(encoded: str) -> str:
    return base64.b64decode(encoded.encode("utf-8")).decode("utf-8")


def chunks(items: Iterable[Any], size: int) -> list[list[Any]]:
    if size <= 0:
        raise errors.invalid_chunk_size()
    data = list(items)
    return [data[i : i + size] for i in range(0, len(data), size)]


def run_command(
    command: Union[str, list[str]],
    timeout: Optional[float] = None,
    check: bool = False,
    shell: bool = False,
) -> subprocess.CompletedProcess:
    return subprocess.run(
        command,
        timeout=timeout,
        check=check,
        shell=shell,
        capture_output=True,
        text=True,
    )


def retry(
    fn: Callable[..., Any],
    *args: Any,
    attempts: int = 3,
    delay_seconds: float = 0.5,
    exceptions: tuple[type[BaseException], ...] = (Exception,),
    **kwargs: Any,
) -> Any:
    if attempts <= 0:
        raise errors.invalid_retry_attempts()

    last_error: Optional[BaseException] = None
    for index in range(attempts):
        try:
            return fn(*args, **kwargs)
        except exceptions as ex:
            last_error = ex
            if index < attempts - 1 and delay_seconds > 0:
                time.sleep(delay_seconds)

    if last_error is not None:
        raise last_error
    raise errors.idk_what_happened()