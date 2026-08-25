"""Tiny Korean console logger. Avoids stdlib logging configuration headaches on Windows."""

from __future__ import annotations

import sys
import time
from typing import Any


_RESET = "\033[0m"
_DIM = "\033[2m"
_BLUE = "\033[34m"
_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_RED = "\033[31m"


def _ensure_utf8_stdout() -> None:
    """Reconfigure stdout/stderr to UTF-8 on Windows so Korean characters print."""
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except (OSError, ValueError):
                pass


_ensure_utf8_stdout()


def _stamp() -> str:
    return time.strftime("%H:%M:%S")


def _emit(color: str, tag: str, message: str) -> None:
    line = f"{_DIM}[{_stamp()}]{_RESET} {color}{tag}{_RESET} {message}"
    try:
        print(line, file=sys.stdout, flush=True)
    except UnicodeEncodeError:
        safe = line.encode("ascii", errors="replace").decode("ascii")
        print(safe, file=sys.stdout, flush=True)


def info(message: str) -> None:
    _emit(_BLUE, "[INFO]", message)


def step(message: str) -> None:
    _emit(_GREEN, "[STEP]", message)


def warn(message: str) -> None:
    _emit(_YELLOW, "[WARN]", message)


def error(message: str) -> None:
    _emit(_RED, "[ERROR]", message)


def cost(usage: dict[str, Any], estimated_usd: float) -> None:
    in_tok = usage.get("input_tokens", 0)
    cw = usage.get("cache_creation_input_tokens", 0)
    cr = usage.get("cache_read_input_tokens", 0)
    out_tok = usage.get("output_tokens", 0)
    msg = (
        f"input {in_tok:,} / cache write {cw:,} / cache read {cr:,} / "
        f"output {out_tok:,} tokens → approx. ${estimated_usd:.4f}"
    )
    _emit(_DIM, "[COST]", msg)
