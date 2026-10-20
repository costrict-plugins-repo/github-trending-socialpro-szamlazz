"""Cross-platform config directory resolution for socialpro-szamlazz.

Lookup priority (first match wins):
  1. $SZAMLAZZ_CONFIG_DIR env var (explicit override)
  2. ./.szamlazz/ (project-local, for multi-tenant workflows)
  3. OS-default global dir:
       - macOS:   ~/Library/Application Support/szamlazz/
                  or ~/.config/szamlazz/ (XDG fallback)
       - Linux:   $XDG_CONFIG_HOME/szamlazz/ (default: ~/.config/szamlazz/)
       - Windows: %APPDATA%\\szamlazz\\
  4. ~/.claude/szamlazz/ (legacy fallback for users migrating from the original skill)

Stdlib-only — no external dependencies.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional


def resolve_config_dir() -> Optional[Path]:
    """Return the first existing config dir, or None if none is set up."""

    # Priority 1 — explicit env var override
    if env := os.environ.get("SZAMLAZZ_CONFIG_DIR"):
        p = Path(env).expanduser()
        if p.is_dir():
            return p

    # Priority 2 — project-local
    local = Path.cwd() / ".szamlazz"
    if local.is_dir():
        return local

    # Priority 3 — OS-default global
    if sys.platform == "win32":
        if appdata := os.environ.get("APPDATA"):
            p = Path(appdata) / "szamlazz"
            if p.is_dir():
                return p
    elif sys.platform == "darwin":
        for candidate in [
            Path.home() / "Library" / "Application Support" / "szamlazz",
            Path.home() / ".config" / "szamlazz",
        ]:
            if candidate.is_dir():
                return candidate
    else:
        xdg = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
        p = Path(xdg) / "szamlazz"
        if p.is_dir():
            return p

    # Priority 4 — legacy ~/.claude/szamlazz/
    legacy = Path.home() / ".claude" / "szamlazz"
    if legacy.is_dir():
        return legacy

    return None


def default_config_dir_for_setup() -> Path:
    """Return the path where the init flow should create new config.

    Uses OS platform conventions. Does NOT create the directory —
    the caller is responsible for mkdir.
    """
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / "szamlazz"
        # Fallback when APPDATA is not set (e.g., minimal CI environments)
        return Path.home() / ".config" / "szamlazz"
    elif sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "szamlazz"
    else:
        xdg = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
        return Path(xdg) / "szamlazz"


def load_agent_key(config_dir: Optional[Path]) -> Optional[str]:
    """Load SZAMLAZZ_AGENT_KEY from env var, falling back to config_dir/.env."""
    if key := os.environ.get("SZAMLAZZ_AGENT_KEY"):
        return key

    if config_dir is None:
        return None

    env_file = config_dir / ".env"
    if not env_file.is_file():
        return None

    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("SZAMLAZZ_AGENT_KEY="):
            value = line.split("=", 1)[1]
            return value.strip().strip('"').strip("'")

    return None
