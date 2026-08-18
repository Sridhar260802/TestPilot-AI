import os
import logging
from groq import Groq, APIStatusError
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

# Groq deprecates/renames chat models frequently, and a name that's valid
# today can 404 tomorrow (as just happened with three hardcoded names in a
# row). Instead of guessing another name, this asks Groq's own /models
# endpoint which models this key can actually use right now, and picks one.
#
# You can still pin a specific model via .env — GROQ_MODEL=<id> — and it'll
# be tried first (and skipped automatically if it's no longer valid).

_MODEL_CACHE = {"id": None}

# Substrings checked in order against the live model list, to prefer a
# capable general-purpose chat model over e.g. whisper/tts/guard models.
_PREFERENCE_ORDER = [
    "llama-3.3-70b",
    "llama-3.1-70b",
    "llama-3.3",
    "llama-3.1",
    "llama3-70b",
    "llama3",
    "mixtral",
    "qwen",
    "deepseek",
    "gemma",
]

_EXCLUDE_SUBSTRINGS = ["whisper", "tts", "guard", "moderation", "vision"]

FALLBACK_MESSAGE = (
    "AI-written recommendations aren't available for this report right now. "
    "All test results above are unaffected — see the scores and module details "
    "for the full findings."
)


def _pick_model_from_list(model_ids):
    usable = [m for m in model_ids if not any(x in m.lower() for x in _EXCLUDE_SUBSTRINGS)]
    for pref in _PREFERENCE_ORDER:
        for m in usable:
            if pref in m.lower():
                return m
    return usable[0] if usable else None


def _discover_model():
    """Fetch the account's available models from Groq and pick one. Cached
    in-process so this only hits the network once per server run (until it
    fails, in which case the next call re-discovers)."""
    if _MODEL_CACHE["id"]:
        return _MODEL_CACHE["id"]

    try:
        listing = client.models.list()
        model_ids = [m.id for m in getattr(listing, "data", [])]
    except Exception as e:
        logger.error("Could not list Groq models: %s", e)
        return None

    if not model_ids:
        logger.error("Groq /models returned no models for this API key.")
        return None

    pinned = os.getenv("GROQ_MODEL")
    if pinned and pinned in model_ids:
        _MODEL_CACHE["id"] = pinned
        return pinned

    chosen = _pick_model_from_list(model_ids)
    if chosen:
        logger.info("Groq model auto-selected: %s (available: %s)", chosen, model_ids)
        _MODEL_CACHE["id"] = chosen
    return chosen


def generate_ai_suggestions(prompt: str) -> str:
    """
    Calls Groq for AI-written suggestions. Never raises — a failure here
    (deprecated/unavailable model, rate limit, network issue, missing API
    key) degrades to a plain-text fallback instead of taking down the whole
    report generation request.
    """
    if not os.getenv("GROQ_API_KEY"):
        logger.warning("GROQ_API_KEY is not set — skipping AI suggestions.")
        return FALLBACK_MESSAGE

    model = _discover_model()
    if not model:
        return FALLBACK_MESSAGE

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        return response.choices[0].message.content
    except APIStatusError as e:
        # Model went bad between discovery and use (e.g. decommissioned
        # mid-run) — clear the cache so the next request re-discovers,
        # and degrade gracefully for this request.
        logger.warning("Cached Groq model '%s' failed (%s) — will rediscover next call.", model, e)
        _MODEL_CACHE["id"] = None
        return FALLBACK_MESSAGE
    except Exception as e:
        logger.error("Groq request failed: %s", e)
        return FALLBACK_MESSAGE