"""Runtime configuration loader. Reads .env and exposes constants."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()

CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6").strip()

_DEFAULT_ELITE_DIR = PROJECT_ROOT / "data" / "elite"
_env_elite = os.getenv("ELITE_DATA_DIR", "").strip()
if _env_elite:
    _p = Path(_env_elite)
    ELITE_DATA_DIR = _p if _p.is_absolute() else (PROJECT_ROOT / _p)
else:
    ELITE_DATA_DIR = _DEFAULT_ELITE_DIR

OUTPUT_DIR = PROJECT_ROOT / "output"
PROMPTS_DIR = PROJECT_ROOT / "src" / "prompts"

# Anthropic Sonnet 4.6 published pricing (per 1M tokens), used only for cost estimates.
PRICE_PER_MTOK_INPUT = 3.0
PRICE_PER_MTOK_CACHE_WRITE = 3.75
PRICE_PER_MTOK_CACHE_READ = 0.30
PRICE_PER_MTOK_OUTPUT = 15.0


def require_api_key() -> str:
    if not ANTHROPIC_API_KEY:
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set. "
            f"Create the {PROJECT_ROOT / '.env'} file and enter your key."
        )
    return ANTHROPIC_API_KEY
