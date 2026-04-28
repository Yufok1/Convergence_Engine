from __future__ import annotations

import json
from pathlib import Path

from security_receipts import (
    facility_access_policy,
    get_action_contract,
    hash_payload,
    read_action_receipts,
    record_action_receipt,
    redact_sensitive,
    receipt_response_metadata,
    validate_action_submission,
)


def test_redacts_sensitive_keys_and_config_patch_values():
    payload = {
        "api_key": "sk-secret",
        "headers": {"Authorization": "Bearer token"},
        "patch": [
            {"op": "replace", "path": "/ollama/api_key", "value": "hf_secret"},
            {"op": "replace", "path": "/simulation/max_steps", "value": 10},
        ],
    }

    redacted = redact_sensitive(payload)

    assert redacted["api_key"] == "[REDACTED]"
    assert redacted["headers"]["Authorization"] == "[REDACTED]"
    assert redacted["patch"][0]["value"] == "[REDACTED]"
    assert redacted["patch"][1]["value"] == 10


def test_record_action_receipt_writes_append_only_jsonl(tmp_path: Path):
    artifact = tmp_path / "artifact.txt"
    artifact.write_text("receipt artifact", encoding="utf-8")

    receipt = record_action_receipt(
        "cocoon_compile",
        actor="test",
        payload={"api_key": "sk-secret", "format": "cocoon"},
        result={"filename": artifact.name},
        artifact_paths=[artifact],
        project_root=tmp_path,
    )

    assert receipt["receipt_id"]
    assert receipt["contract"]["risk"] == "high"
    assert receipt["contract"]["access_mode"] == "explicit_only"
    assert receipt["payload_hash"] == hash_payload({"api_key": "sk-secret", "format": "cocoon"})
    assert receipt["payload_preview"]["api_key"] == "[REDACTED]"
    assert receipt["artifacts"][0]["exists"] is True

    rows = read_action_receipts(project_root=tmp_path, limit=10)
    assert len(rows) == 1
    assert rows[0]["action"] == "cocoon_compile"
    assert rows[0]["payload_preview"]["api_key"] == "[REDACTED]"

    receipt_path = tmp_path / "data" / "security_receipts" / "action_receipts.jsonl"
    assert len(receipt_path.read_text(encoding="utf-8").splitlines()) == 1
    assert json.loads(receipt_path.read_text(encoding="utf-8").splitlines()[0])["action"] == "cocoon_compile"


def test_contract_metadata_and_default_confirmation_gate():
    contract = get_action_contract("checkpoint_restore")
    assert contract["requires_confirmation"] is True
    assert "training_state" in contract["markings"]
    assert contract["access_mode"] == "explicit_only"

    ok, error = validate_action_submission("checkpoint_restore", {})
    assert ok is True
    assert error is None


def test_receipt_response_metadata_is_small():
    metadata = receipt_response_metadata(
        {
            "receipt_id": "rec_test",
            "timestamp": "2026-04-28T00:00:00Z",
            "action": "config_update",
            "status": "ok",
            "payload_hash": "abc",
            "result_hash": "def",
            "contract": get_action_contract("config_update"),
            "artifacts": [{"path": "config.json"}],
        }
    )

    assert metadata == {
        "receipt_id": "rec_test",
        "timestamp": "2026-04-28T00:00:00Z",
        "action": "config_update",
        "status": "ok",
        "payload_hash": "abc",
        "result_hash": "def",
        "markings": ["operator_only", "runtime_mutation", "config_write"],
        "risk": "high",
        "scope": "runtime_config",
        "access_mode": "explicit_only",
        "artifacts": [{"path": "config.json"}],
    }


def test_facility_policy_separates_safe_default_from_explicit_only():
    policy = facility_access_policy()

    assert policy["default_mode"] == "read_observe_status_log_search_only"
    assert policy["safe_default_verbs"] == ["read", "observe", "status", "log", "search"]
    assert policy["safe_default_actions"] == []
    assert "research_notepad_add" in policy["explicit_only_actions"]
    assert "manual_receipt" in policy["explicit_only_actions"]
    assert "butterfly_chat" in policy["explicit_only_actions"]
    assert "cocoon_compile" in policy["explicit_only_actions"]
    assert "remote_exec" in policy["denied_by_default"]
