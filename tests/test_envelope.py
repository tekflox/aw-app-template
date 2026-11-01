"""Coverage for template_app/envelope.py.

TEMPLATE: pure-function tests, no FastAPI runtime and no WebSocket client —
that the envelope helpers need neither is the point of keeping transport out
of that module.

Run: .venv/aw/bin/python -m pytest tests/test_envelope.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from template_app.envelope import (  # noqa: E402
    ERROR_TYPE,
    PROTOCOL,
    domain_for,
    error_frame,
    frame,
    init_frame,
    is_conforming,
)


# --- domain_for -----------------------------------------------------------

def test_domain_for_collapses_every_dash():
    assert domain_for("aw-app-template") == "aw_app_template"


def test_domain_for_leaves_a_dashless_slug_alone():
    assert domain_for("devctl") == "devctl"


def test_domain_for_rejects_an_empty_slug():
    with pytest.raises(ValueError, match="non-empty"):
        domain_for("")


# --- frame ----------------------------------------------------------------

def test_frame_defaults_data_to_an_empty_object():
    assert frame("aw_app_template_ping") == {
        "type": "aw_app_template_ping",
        "data": {},
    }


def test_frame_keeps_the_data_it_is_given():
    assert frame("aw_app_template_echo", {"text": "hi"}) == {
        "type": "aw_app_template_echo",
        "data": {"text": "hi"},
    }


def test_frame_omits_id_and_re_when_not_given():
    assert set(frame("aw_app_template_ping")) == {"type", "data"}


def test_frame_includes_id_and_re_when_given():
    assert frame("aw_app_template_echo", {}, id="a1", re="b2") == {
        "type": "aw_app_template_echo",
        "data": {},
        "id": "a1",
        "re": "b2",
    }


@pytest.mark.parametrize(
    "bad",
    [
        "init",                      # bare word, no <domain>_<event>
        "aw_app_template_Echo",      # not lowercase
        "aw-app-template_echo",      # dashes, not underscores
        "aw_app_template_",          # trailing separator
        "_echo",                     # leading separator
        "",
    ],
)
def test_frame_rejects_a_non_conforming_type(bad):
    with pytest.raises(ValueError, match="snake_case"):
        frame(bad)


def test_frame_rejects_a_non_string_type():
    with pytest.raises(ValueError, match="snake_case"):
        frame(None)


@pytest.mark.parametrize("bad", [[], "text", 1, ("a",)])
def test_frame_rejects_data_that_is_not_an_object(bad):
    with pytest.raises(ValueError, match="must be an object"):
        frame("aw_app_template_echo", bad)


# --- init_frame -----------------------------------------------------------

def test_init_frame_carries_the_protocol_version():
    assert init_frame("aw_app_template") == {
        "type": "aw_app_template_init",
        "data": {"protocol": PROTOCOL},
    }


def test_init_frame_merges_extra_capabilities():
    got = init_frame("aw_app_template", features=["echo"])
    assert got["data"] == {"features": ["echo"], "protocol": PROTOCOL}


def test_init_frame_does_not_let_extra_override_the_protocol():
    assert init_frame("aw_app_template", protocol=99)["data"]["protocol"] == PROTOCOL


# --- error_frame ----------------------------------------------------------

def test_error_frame_is_not_domain_prefixed():
    got = error_frame("invalid_json", "frame was not valid JSON")
    assert got == {
        "type": ERROR_TYPE,
        "data": {"code": "invalid_json", "message": "frame was not valid JSON"},
    }
    assert got["type"] == "error"


# --- is_conforming --------------------------------------------------------

def test_is_conforming_accepts_a_minimal_frame():
    assert is_conforming({"type": "aw_app_template_echo", "data": {}})


def test_is_conforming_accepts_optional_string_id_and_re():
    assert is_conforming(
        {"type": "aw_app_template_echo", "data": {}, "id": "a", "re": "b"}
    )


def test_is_conforming_accepts_an_unrecognised_type():
    # Shape-only by design: an unknown type is still conforming, and the
    # caller must ignore it rather than close the socket.
    assert is_conforming({"type": "some_other_event", "data": {}})


@pytest.mark.parametrize(
    "bad",
    [
        None,
        [],
        "text",
        {},                                              # no type, no data
        {"type": "aw_app_template_echo"},                # missing data
        {"data": {}},                                    # missing type
        {"type": 1, "data": {}},                         # type not a string
        {"type": "aw_app_template_echo", "data": []},    # data not an object
        {"type": "aw_app_template_echo", "data": None},
    ],
)
def test_is_conforming_rejects_malformed_frames(bad):
    assert not is_conforming(bad)


@pytest.mark.parametrize("key", ["id", "re"])
def test_is_conforming_rejects_a_non_string_id_or_re(key):
    assert not is_conforming(
        {"type": "aw_app_template_echo", "data": {}, key: 7}
    )
