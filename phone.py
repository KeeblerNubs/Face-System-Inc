from __future__ import annotations

import os
import re
from typing import Any, Optional

import httpx
import phonenumbers
from phonenumbers import carrier, geocoder, timezone
from phonenumbers.phonenumberutil import NumberParseException

NUMVERIFY_API_KEY_ENV = "NUMVERIFY_API_KEY"
NUMVERIFY_URL = "http://apilayer.net/api/validate"
NUMVERIFY_TIMEOUT = 10.0

_DIGITS_AND_PLUS = re.compile(r"[^\d+]")

LINE_TYPES = {
    phonenumbers.PhoneNumberType.FIXED_LINE: "fixed_line",
    phonenumbers.PhoneNumberType.MOBILE: "mobile",
    phonenumbers.PhoneNumberType.FIXED_LINE_OR_MOBILE: "fixed_line_or_mobile",
    phonenumbers.PhoneNumberType.TOLL_FREE: "toll_free",
    phonenumbers.PhoneNumberType.PREMIUM_RATE: "premium_rate",
    phonenumbers.PhoneNumberType.SHARED_COST: "shared_cost",
    phonenumbers.PhoneNumberType.VOIP: "voip",
    phonenumbers.PhoneNumberType.PERSONAL_NUMBER: "personal_number",
    phonenumbers.PhoneNumberType.PAGER: "pager",
    phonenumbers.PhoneNumberType.UAN: "uan",
    phonenumbers.PhoneNumberType.VOICEMAIL: "voicemail",
    phonenumbers.PhoneNumberType.UNKNOWN: "unknown",
}


def validate_phone_input(raw: str) -> str:
    """Sanitize and minimally validate a user-supplied phone string.

    Accepts digits, `+`, spaces, dashes, dots, and parentheses. Returns the
    stripped E.164-compatible candidate (digits with optional leading `+`).
    """
    if not raw or not raw.strip():
        raise ValueError("Phone number must not be empty.")

    cleaned = _DIGITS_AND_PLUS.sub("", raw)
    if not cleaned:
        raise ValueError("Phone number must contain digits.")
    if cleaned.count("+") > 1 or ("+" in cleaned and not cleaned.startswith("+")):
        raise ValueError("Phone number may only contain a single leading '+'.")
    if len(cleaned.lstrip("+")) < 4:
        raise ValueError("Phone number is too short to be valid.")
    if len(cleaned.lstrip("+")) > 15:
        raise ValueError("Phone number is too long to be valid (E.164 max is 15 digits).")
    return cleaned


def lookup_phone(raw: str, default_region: Optional[str] = None) -> dict[str, Any]:
    """Parse and enrich a phone number with offline metadata.

    Uses the `phonenumbers` library (Google's libphonenumber port) to return
    country, region, carrier, timezones, line type, and multiple canonical
    format strings. No network calls.
    """
    candidate = validate_phone_input(raw)
    region = default_region.upper() if default_region else None

    try:
        parsed = phonenumbers.parse(candidate, region)
    except NumberParseException as exc:
        raise ValueError(f"Could not parse phone number: {exc}") from exc

    is_possible = phonenumbers.is_possible_number(parsed)
    is_valid = phonenumbers.is_valid_number(parsed)
    number_type = LINE_TYPES.get(
        phonenumbers.number_type(parsed), "unknown"
    )

    country_code = parsed.country_code
    region_code = phonenumbers.region_code_for_number(parsed)
    location = geocoder.description_for_number(parsed, "en") or None
    carrier_name = carrier.name_for_number(parsed, "en") or None
    timezones = list(timezone.time_zones_for_number(parsed))

    formats = {
        "e164": phonenumbers.format_number(
            parsed, phonenumbers.PhoneNumberFormat.E164
        ),
        "international": phonenumbers.format_number(
            parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL
        ),
        "national": phonenumbers.format_number(
            parsed, phonenumbers.PhoneNumberFormat.NATIONAL
        ),
        "rfc3966": phonenumbers.format_number(
            parsed, phonenumbers.PhoneNumberFormat.RFC3966
        ),
    }

    return {
        "input": raw,
        "valid": is_valid,
        "possible": is_possible,
        "country_code": country_code,
        "region_code": region_code,
        "location": location,
        "carrier": carrier_name,
        "line_type": number_type,
        "timezones": timezones,
        "formats": formats,
    }


async def numverify_lookup(raw: str, api_key: Optional[str] = None) -> Optional[dict[str, Any]]:
    """Optionally enrich a phone number via the Numverify API.

    Returns None if no API key is configured. Raises httpx errors on transport
    failures and ValueError if the API reports an error payload.
    """
    key = api_key or os.getenv(NUMVERIFY_API_KEY_ENV)
    if not key:
        return None

    candidate = validate_phone_input(raw)
    params = {"access_key": key, "number": candidate, "format": "1"}

    async with httpx.AsyncClient(timeout=NUMVERIFY_TIMEOUT) as client:
        resp = await client.get(NUMVERIFY_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

    if isinstance(data, dict) and data.get("success") is False:
        info = data.get("error", {})
        raise ValueError(
            f"Numverify error: {info.get('info') or info.get('type') or 'unknown error'}"
        )

    return data


async def reverse_phone_lookup(
    raw: str,
    default_region: Optional[str] = None,
    use_numverify: bool = False,
) -> dict[str, Any]:
    """Full reverse phone lookup combining offline metadata and optional Numverify."""
    result = lookup_phone(raw, default_region=default_region)

    if use_numverify:
        try:
            numverify = await numverify_lookup(raw)
        except (httpx.HTTPError, ValueError) as exc:
            numverify = {"error": str(exc)}
        if numverify is not None:
            result["numverify"] = numverify

    return result
