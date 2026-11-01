"""Reusable ``aw-ws/1`` envelope helpers (standard
docs/standards/app-backend-websocket-messaging.md in the aw-workspace repo).

``routes.py`` documents the envelope rules in full and then open-codes them
inline: it builds ``{"type": f"{_DOMAIN}_init", ...}`` by f-string and
validates inbound frames with a three-clause ``if``. That is fine for one
socket, but this repo is the template every new ``aw-app-*`` is born from,
so each new app currently re-derives the same four rules by reading a
docstring — which is exactly how one app ends up sending ``data`` as a bare
list, or a domain built with ``-`` instead of ``_``.

This module is that derivation done once:

* :func:`domain_for` turns an app slug into the ``<domain>`` token
  mechanically, so nobody has to remember the ``-`` to ``_`` rule.
* :func:`frame` builds a conforming envelope and refuses to build a
  non-conforming one.
* :func:`is_conforming` is the inbound check, and
* :func:`error_frame` is the one error shape every socket must answer with.

Deliberately NOT here: transport. Nothing in this module touches a
WebSocket, which is what keeps it testable without a client and reusable by
anything that needs the envelope shape (an HTTP SSE stream, a test double).

Binary frames are exempt from the envelope entirely (standard §4.5) and so
are outside this module's scope — there is no ``bytes`` path to find here.
"""
from __future__ import annotations

import re as _re
from typing import Any

#: The envelope version carried in an init frame's ``data.protocol``.
PROTOCOL = 1

#: The one error ``type`` every socket answers malformed input with — not a
#: domain-prefixed variant, so a single client handler covers every socket
#: in the workspace (standard §6.6).
ERROR_TYPE = "error"

#: A ``<domain>_<event>`` token: lowercase snake_case, and at least one
#: ``_`` since every type is a domain AND an event, never a bare word.
_TYPE_RE = _re.compile(r"^[a-z0-9]+(?:_[a-z0-9]+)+$")


def domain_for(slug: str) -> str:
    """Return the ``<domain>`` token for an app ``slug``.

    Every ``-`` collapses to ``_`` — mechanically, not by taste. For this
    repo's ``aw-app-template`` that yields ``aw_app_template``, which reads
    oddly stacked next to ``_init``; that ugliness is the point of a
    mechanical rule, so resist "fixing" it.
    """
    if not slug:
        raise ValueError("slug must be a non-empty string")
    return slug.replace("-", "_")


def frame(
    type_: str,
    data: dict[str, Any] | None = None,
    *,
    id: str | None = None,
    re: str | None = None,
) -> dict[str, Any]:
    """Build one conforming ``aw-ws/1`` frame.

    ``data`` defaults to ``{}`` rather than being omitted: the standard wants
    an object always, even when empty, never a missing key and never a bare
    scalar or array.

    ``id`` and ``re`` are included only when given, so a frame that expects
    no reply does not carry a null correlation id that a client might then
    try to answer.
    """
    if not isinstance(type_, str) or not _TYPE_RE.match(type_):
        raise ValueError(
            f"type must be lowercase <domain>_<event> snake_case, got {type_!r}"
        )
    if data is None:
        data = {}
    if not isinstance(data, dict):
        raise ValueError(f"data must be an object, got {type(data).__name__}")

    out: dict[str, Any] = {"type": type_, "data": data}
    if id is not None:
        out["id"] = id
    if re is not None:
        out["re"] = re
    return out


def init_frame(domain: str, **extra: Any) -> dict[str, Any]:
    """Build the frame every socket must send first, unconditionally.

    ``extra`` is merged into ``data`` alongside ``protocol``, for the app
    that wants to advertise capabilities in the same breath. ``protocol`` is
    set last so a caller cannot accidentally claim a version this module does
    not implement.
    """
    return frame(f"{domain}_init", {**extra, "protocol": PROTOCOL})


def error_frame(code: str, message: str) -> dict[str, Any]:
    """Build the literal error frame malformed input is answered with.

    Note this is the one frame whose ``type`` is NOT ``<domain>_<event>``, so
    it bypasses :func:`frame`'s type check by construction rather than by
    exception.
    """
    return {"type": ERROR_TYPE, "data": {"code": code, "message": message}}


def is_conforming(value: Any) -> bool:
    """Whether ``value`` is a well-formed envelope.

    Checks shape only — a conforming frame whose ``type`` this app does not
    recognise is still conforming, and callers must ignore it rather than
    close the socket (standard §6.5). That separation is the whole reason
    this returns a bool instead of raising.
    """
    if not isinstance(value, dict):
        return False
    if not isinstance(value.get("type"), str):
        return False
    if not isinstance(value.get("data"), dict):
        return False
    for optional in ("id", "re"):
        if optional in value and not isinstance(value[optional], str):
            return False
    return True
