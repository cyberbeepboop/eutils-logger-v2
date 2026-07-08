# eutils-logger

A configurable logger API for Python with easy config files and utility helpers.

## Install

### From local clone

```bash
pip install -r requirements.txt
```

### As package (editable, recommended for development)

```bash
pip install -e .
```

### From a GitHub release

Download the release assets from the repository Releases page, then install the wheel:

```bash
pip install eutils_logger-0.1.1-py3-none-any.whl
```

If you want the source package instead, download the `.tar.gz` and install it with:

```bash
pip install eutils-logger-0.1.1.tar.gz
```

## Quick Start

```python
from eutils_logger import Logger

logger = Logger()
logger.info("Hello world")
logger.error("Something failed", user="API")
```

## Config

Create a `config.yml` in your project root:

```yaml
time_format: "[%H:%M:%S]"
default_user: "System"
log_file: "log.log"
include_timestamp: true
include_level: true
separator: " | "
file_mode: "a"
write_to_console: false
auto_create_dirs: true
enabled_levels:
  - DEBUG
  - INFO
  - WARNING
  - ERROR
  - CRITICAL
```

## API

- `Logger.write(message, user=None, level="INFO")`
- `Logger.debug/info/warning/error/critical(...)`
- `get_config(config_path=None)`
- `update_config(updates, config_path="config.yml")`
- `save_config(config, config_path="config.yml")`
- `clear_log(log_file=None, config_path=None)`
- Backward-compatible: `log("message")`

## Project Layout

- `other/eutils.py`: utility helpers
- `other/eutils_logger.py`: logger implementation
- `eutils.py`: top-level import shim
- `eutils_logger.py`: top-level import shim

## Release

The repository is configured to build release artifacts from tagged versions.

1. Bump the version in `pyproject.toml`
2. Create a tag like `v0.1.1`
3. Push the tag to GitHub
4. GitHub Actions will build and attach the wheel and source archive to the release
