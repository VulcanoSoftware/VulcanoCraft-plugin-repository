"""Gedeelde HTTP-helper voor alle fetchers.

Waarom bestaat dit?
Elke fetcher deed voorheen kale ``requests.get(url)`` calls: geen timeout, geen
identificerende User-Agent en geen retry. Tijdens een cron-cyclus (honderden
plugins achter elkaar) leverde dat structureel mislukte calls op door
rate limiting (429), tijdelijke 5xx-fouten of hangende verbindingen. Een
mislukte call betekent een lege titel/versie/loader, en dat is precies wat in
de UI als "Geen titel" / "Geen versies" verscheen.

Deze helper:
- zet een identificerende User-Agent (Modrinth e.d. vragen daar expliciet om),
- zet een standaard timeout zodat een fetcher nooit eindeloos blijft hangen,
- herhaalt de call bij 429/5xx en bij verbindingsfouten (met backoff en
  respect voor ``Retry-After``),
- stuurt een GitHub-token mee (``GITHUB_TOKEN`` of ``GH_TOKEN``), maar uitsluitend
  naar ``api.github.com``, om de onbeschreven limiet van 60 requests/uur te vermijden.

Er wordt bewust ``requests.get`` aangeroepen (geen Session), zodat bestaande
``patch('requests.get')``-mocks in de tests blijven werken.
"""

import os
import time
from urllib.parse import urlparse

import requests

DEFAULT_USER_AGENT = (
    "VulcanoCraft-Plugin-Repository/1.0 "
    "(+https://github.com/VulcanoSoftware/VulcanoCraft-plugin-repository)"
)
DEFAULT_TIMEOUT = 15
MAX_ATTEMPTS = 3
BACKOFF_BASE_SECONDS = 1.0
MAX_RETRY_AFTER_SECONDS = 15.0
RETRY_STATUS_CODES = frozenset({429, 500, 502, 503, 504})


def _github_token():
    return os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")


def _build_headers(url, headers):
    merged = dict(headers or {})
    # Header-namen zijn case-insensitive: niet overschrijven wat de caller zelf zet.
    lowered = {k.lower() for k in merged}
    if "user-agent" not in lowered:
        merged["User-Agent"] = DEFAULT_USER_AGENT

    token = _github_token()
    if token and "authorization" not in lowered:
        try:
            host = (urlparse(url).hostname or "").lower()
        except ValueError:
            host = ""
        # Token nooit naar andere hosts sturen.
        if host == "api.github.com":
            merged["Authorization"] = f"Bearer {token}"
    return merged


def _retry_delay(response, attempt):
    delay = BACKOFF_BASE_SECONDS * (2 ** attempt)
    retry_after = None
    try:
        retry_after = response.headers.get("Retry-After")
    except Exception:
        retry_after = None
    if retry_after is not None:
        try:
            delay = max(delay, float(retry_after))
        except (TypeError, ValueError):
            pass
    return min(delay, MAX_RETRY_AFTER_SECONDS)


def http_get(url, headers=None, timeout=None, **kwargs):
    """Drop-in vervanger voor ``requests.get`` met timeout, User-Agent en retry.

    Gedrag bij falen is gelijk aan ``requests.get``: na het opgebruiken van de
    pogingen wordt bij een netwerkfout de laatste exception opnieuw geraised, en
    bij een blijvende 429/5xx wordt de laatste response teruggegeven zodat de
    caller zijn eigen ``raise_for_status()`` / ``status_code``-afhandeling houdt.
    """
    merged_headers = _build_headers(url, headers)
    effective_timeout = DEFAULT_TIMEOUT if timeout is None else timeout

    last_exc = None
    for attempt in range(MAX_ATTEMPTS):
        is_last = attempt == MAX_ATTEMPTS - 1
        try:
            response = requests.get(
                url, headers=merged_headers, timeout=effective_timeout, **kwargs
            )
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as exc:
            last_exc = exc
            if is_last:
                raise
            time.sleep(BACKOFF_BASE_SECONDS * (2 ** attempt))
            continue

        status = getattr(response, "status_code", None)
        if isinstance(status, int) and status in RETRY_STATUS_CODES and not is_last:
            time.sleep(_retry_delay(response, attempt))
            continue
        return response

    # Onbereikbaar in de praktijk (de laatste poging returnt of raiset), maar
    # houdt de functie ook formeel waterdicht.
    if last_exc is not None:
        raise last_exc
    raise requests.exceptions.RequestException(f"Geen response ontvangen voor {url}")
