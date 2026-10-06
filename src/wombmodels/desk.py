"""Read-only loopback discovery of ResearchDesk's ectogenesis blueprint."""
from __future__ import annotations

import ipaddress
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

from .artifacts import InputError, decode_json

MAX_RESPONSE_BYTES = 2_000_000
REQUEST_TIMEOUT_SECONDS = 30


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise InputError("ResearchDesk redirects are not followed")


def desk_endpoint(url):
    try:
        parsed = urlsplit(url)
        host = ipaddress.ip_address(parsed.hostname or "")
        port = parsed.port
    except (TypeError, ValueError) as exc:
        raise InputError("ResearchDesk URL must use a numeric loopback host") from exc
    if (parsed.scheme not in {"http", "https"} or not host.is_loopback
            or parsed.username is not None or parsed.password is not None
            or parsed.path not in {"", "/"} or parsed.query or parsed.fragment
            or (port is not None and not 1 <= port <= 65535)):
        raise InputError("ResearchDesk URL must be a bare HTTP(S) loopback origin without credentials")
    return f"{parsed.scheme}://{parsed.netloc}/api/state"


def desk_status(url="http://127.0.0.1:8092"):
    endpoint = desk_endpoint(url)
    opener = build_opener(ProxyHandler({}), NoRedirect())
    try:
        with opener.open(Request(endpoint, headers={"Accept": "application/json",
                                                    "User-Agent": "wombmodels/0.2.1"}), timeout=REQUEST_TIMEOUT_SECONDS) as response:
            raw = response.read(MAX_RESPONSE_BYTES + 1)
    except (HTTPError, URLError, OSError, TimeoutError) as exc:
        raise InputError("ResearchDesk did not return a usable local response") from exc
    if len(raw) > MAX_RESPONSE_BYTES:
        raise InputError("ResearchDesk response exceeds the 2 MB limit")
    try:
        state = decode_json(raw)
    except InputError as exc:
        raise InputError("ResearchDesk response must be valid bounded UTF-8 JSON with finite numbers") from exc
    if not isinstance(state, dict) or not isinstance(state.get("blueprints"), list):
        raise InputError("ResearchDesk response does not contain a blueprint inventory")
    blueprint = next((item for item in state["blueprints"]
                      if isinstance(item, dict) and item.get("id") == "ectogenesis"), None)
    def identifiers(key):
        group = state.get(key, {})
        entries = group.get("ectogenesis", []) if isinstance(group, dict) else []
        return sorted({item["id"] for item in entries
                       if isinstance(item, dict) and isinstance(item.get("id"), str)
                       and len(item["id"]) <= 96}) if isinstance(entries, list) else []

    title = blueprint.get("title", "") if blueprint else ""
    return {"ectogenesis_blueprint_present": blueprint is not None,
            "title": title[:200] if isinstance(title, str) else "",
            "starter_ids": identifiers("campaign_starters"),
            "framework_axis_ids": identifiers("campaign_frameworks"),
            "bridge_scope": "Read-only blueprint discovery; no private records, jobs or live controls exported."}
