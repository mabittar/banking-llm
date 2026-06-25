"""TASK-09 — shared masking and the privacy invariant from the SPEC."""

from src.core.observability.masking import (
    mask_attr,
    mask_log_event,
    mask_pix_key,
    mask_sensitive_data,
)


def test_mask_sensitive_data_masks_known_keys():
    payload = {
        "authorization": "Bearer abc",
        "government_id": "12345678900",
        "nested": {"jwt_secret": "xyz", "amount": 10},
    }

    masked = mask_sensitive_data(payload)

    assert masked["authorization"] == "********"
    assert masked["government_id"] == "********"
    assert masked["nested"]["jwt_secret"] == "********"
    assert masked["nested"]["amount"] == 10


def test_mask_pix_key_email_and_phone():
    assert mask_pix_key("john@email.com") == "***@email.com"
    assert mask_pix_key("11999998888").endswith("8888")
    assert mask_pix_key("11999998888").startswith("***")


def test_mask_attr_pix_key_attribute_never_full():
    full_key = "john.doe@email.com"

    masked = mask_attr("pix.key.masked", full_key)

    assert full_key not in masked
    assert masked == "***@email.com"


def test_privacy_invariant_no_full_secret_in_attributes():
    sensitive = {
        "token": "supersecrettoken",
        "pix.key": "john@email.com",
        "transaction-hash-key": "deadbeef",
    }

    for key, value in sensitive.items():
        masked = mask_attr(key, value)
        assert value not in str(masked) or masked.startswith("***")


def test_mask_log_event_masks_pix_key_and_secrets():
    event = {
        "event": "Pix withdraw node",
        "pix_key": "john.doe@email.com",
        "token": "supersecret",
        "withdraw_amount": "10.00",
    }

    masked = mask_log_event(None, "info", event)

    assert masked["pix_key"] == "***@email.com"
    assert masked["token"] == "********"
    assert masked["withdraw_amount"] == "10.00"
    assert masked["event"] == "Pix withdraw node"


def test_mask_log_event_masks_nested_payloads():
    event = {"event": "request", "body": {"authorization": "Bearer x", "ok": 1}}

    masked = mask_log_event(None, "info", event)

    assert masked["body"]["authorization"] == "********"
    assert masked["body"]["ok"] == 1
