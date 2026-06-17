"""Module-global Aethex SDK client, constructed once at import time.

The SDK reads the API key and sends ``X-API-Key`` on every request. ``base_url``
is passed only when an explicit override (e.g. staging) is configured; otherwise
the SDK's production default is used. We deliberately do NOT inject a custom
``httpx`` client: the SDK's internal client is what carries the ``base_url`` and
injects the ``X-API-Key`` auth header, so replacing it would break auth.
"""

from aethexai import AethexAI

from aethexai_mcp import config

_kwargs = {"base_url": config.BASE_URL} if config.BASE_URL else {}

client = AethexAI(
    api_key=config.API_KEY,
    timeout=config.TIMEOUT,
    **_kwargs,
)
