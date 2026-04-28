from __future__ import annotations

import hashlib
import json
import os
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

RECEIPT_VERSION = 1
DEFAULT_RECEIPT_PATH = Path("data") / "security_receipts" / "action_receipts.jsonl"

_WRITE_LOCK = threading.RLock()

SENSITIVE_KEY_FRAGMENTS = (
    "api_key",
    "apikey",
    "authorization",
    "bearer",
    "credential",
    "password",
    "secret",
    "token",
)

SENSITIVE_PATH_FRAGMENTS = (
    "api_key",
    "apikey",
    "authorization",
    "credential",
    "password",
    "secret",
    "token",
)

ACTION_CONTRACTS: dict[str, dict[str, Any]] = {
    "config_update": {
        "risk": "high",
        "scope": "runtime_config",
        "markings": ["operator_only", "runtime_mutation", "config_write"],
        "access_mode": "explicit_only",
        "requires_confirmation": True,
        "receipt_mode": "payload_hash_with_redacted_preview",
    },
    "config_rollback": {
        "risk": "high",
        "scope": "runtime_config",
        "markings": ["operator_only", "runtime_mutation", "config_write"],
        "access_mode": "explicit_only",
        "requires_confirmation": True,
        "receipt_mode": "payload_hash_with_redacted_preview",
    },
    "checkpoint_save": {
        "risk": "medium",
        "scope": "neural_checkpoint",
        "markings": ["operator_only", "training_state"],
        "access_mode": "explicit_only",
        "requires_confirmation": False,
        "receipt_mode": "payload_hash_with_artifacts",
    },
    "checkpoint_restore": {
        "risk": "high",
        "scope": "neural_checkpoint",
        "markings": ["operator_only", "runtime_mutation", "training_state"],
        "access_mode": "explicit_only",
        "requires_confirmation": True,
        "receipt_mode": "payload_hash_with_artifacts",
    },
    "simulation_start": {
        "risk": "medium",
        "scope": "simulation_control",
        "markings": ["operator_only", "runtime_mutation"],
        "access_mode": "explicit_only",
        "requires_confirmation": False,
        "receipt_mode": "payload_hash_with_redacted_preview",
    },
    "simulation_stop": {
        "risk": "medium",
        "scope": "simulation_control",
        "markings": ["operator_only", "runtime_mutation"],
        "access_mode": "explicit_only",
        "requires_confirmation": False,
        "receipt_mode": "payload_hash_with_redacted_preview",
    },
    "research_notepad_add": {
        "risk": "low",
        "scope": "scientific_notepad",
        "markings": ["research_log", "operator_visible"],
        "access_mode": "explicit_only",
        "requires_confirmation": False,
        "receipt_mode": "hash_only_content",
    },
    "research_notepad_sync": {
        "risk": "low",
        "scope": "scientific_notepad",
        "markings": ["research_log", "operator_visible"],
        "access_mode": "explicit_only",
        "requires_confirmation": False,
        "receipt_mode": "hash_only_content",
    },
    "research_notepad_clear": {
        "risk": "high",
        "scope": "scientific_notepad",
        "markings": ["operator_only", "destructive"],
        "access_mode": "explicit_only",
        "requires_confirmation": True,
        "receipt_mode": "payload_hash_with_redacted_preview",
    },
    "butterfly_chat": {
        "risk": "medium",
        "scope": "language_training",
        "markings": ["learning_surface", "organism_interaction"],
        "access_mode": "explicit_only",
        "requires_confirmation": False,
        "receipt_mode": "message_hash_only",
    },
    "organism_chat": {
        "risk": "medium",
        "scope": "language_training",
        "markings": ["learning_surface", "organism_interaction"],
        "access_mode": "explicit_only",
        "requires_confirmation": False,
        "receipt_mode": "message_hash_only",
    },
    "cocoon_compile": {
        "risk": "high",
        "scope": "agent_export",
        "markings": ["exportable_artifact", "cocoon_untrusted", "operator_only"],
        "access_mode": "explicit_only",
        "requires_confirmation": True,
        "receipt_mode": "payload_hash_with_artifacts",
    },
    "manual_receipt": {
        "risk": "low",
        "scope": "operator_receipt",
        "markings": ["operator_visible"],
        "access_mode": "explicit_only",
        "requires_confirmation": False,
        "receipt_mode": "payload_hash_with_redacted_preview",
    },
}

FACILITY_ACCESS_POLICY = {
    "default_mode": "read_observe_status_log_search_only",
    "safe_default_verbs": ["read", "observe", "status", "log", "search"],
    "safe_default_actions": [
        action
        for action, contract in ACTION_CONTRACTS.items()
        if contract.get("access_mode") == "safe_default"
    ],
    "explicit_only_actions": [
        action
        for action, contract in ACTION_CONTRACTS.items()
        if contract.get("access_mode") == "explicit_only"
    ],
    "denied_by_default": [
        "clear_all_data",
        "agent_delegate",
        "delegation_escalation",
        "remote_exec",
        "ssh_control",
        "slot_plug",
        "tool_plug",
    ],
    "delegation_rule": "Child or delegated runtimes must never exceed the parent/caller grant ceiling.",
    "rule": (
        "Facility adapters should grant only read/observe/status/log/search by default. "
        "Runtime mutation, config writes, training, export, remote execution, and slot wiring "
        "must be explicitly granted by the operator and receipt-logged."
    ),
}


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def get_action_contract(action: str) -> dict[str, Any]:
    contract = ACTION_CONTRACTS.get(action, {})
    return {
        "action": action,
        "risk": contract.get("risk", "unknown"),
        "scope": contract.get("scope", "unknown"),
        "markings": list(contract.get("markings", ["unclassified_action"])),
        "access_mode": contract.get("access_mode", "explicit_only"),
        "requires_confirmation": bool(contract.get("requires_confirmation", False)),
        "receipt_mode": contract.get("receipt_mode", "payload_hash_with_redacted_preview"),
    }


def list_action_contracts() -> list[dict[str, Any]]:
    return [get_action_contract(action) for action in sorted(ACTION_CONTRACTS)]


def facility_access_policy() -> dict[str, Any]:
    policy = dict(FACILITY_ACCESS_POLICY)
    policy["safe_default_actions"] = sorted(policy["safe_default_actions"])
    policy["explicit_only_actions"] = sorted(policy["explicit_only_actions"])
    policy["denied_by_default"] = sorted(policy["denied_by_default"])
    return policy


def action_confirmation_required() -> bool:
    return os.environ.get("CONVERGENCE_REQUIRE_ACTION_CONFIRMATION", "").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def validate_action_submission(action: str, payload: Mapping[str, Any] | None) -> tuple[bool, str | None]:
    contract = get_action_contract(action)
    if not action_confirmation_required() or not contract["requires_confirmation"]:
        return True, None

    payload = payload or {}
    confirmation = payload.get("confirmation") or payload.get("confirm")
    if confirmation is True or str(confirmation).strip().lower() in {action.lower(), "true", "confirmed"}:
        return True, None
    return False, (
        f"Action '{action}' requires explicit confirmation when "
        "CONVERGENCE_REQUIRE_ACTION_CONFIRMATION is enabled."
    )


def redact_sensitive(value: Any) -> Any:
    if isinstance(value, Mapping):
        lower_keys = {str(k).lower(): k for k in value.keys()}
        path_value = str(value.get("path", "")).lower()
        path_is_sensitive = any(fragment in path_value for fragment in SENSITIVE_PATH_FRAGMENTS)
        out: dict[str, Any] = {}
        for key, item in value.items():
            key_text = str(key).lower()
            if any(fragment in key_text for fragment in SENSITIVE_KEY_FRAGMENTS):
                out[str(key)] = "[REDACTED]"
            elif path_is_sensitive and key_text in {"value", "old_value", "new_value"}:
                out[str(key)] = "[REDACTED]"
            else:
                out[str(key)] = redact_sensitive(item)
        if "authorization" in lower_keys:
            out[str(lower_keys["authorization"])] = "[REDACTED]"
        return out
    if isinstance(value, (list, tuple, set)):
        return [redact_sensitive(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, str):
        lower = value.lower()
        if lower.startswith("bearer ") or lower.startswith("hf_") or lower.startswith("sk-"):
            return "[REDACTED]"
    return value


def _json_default(value: Any) -> str:
    return str(value)


def canonical_json(value: Any) -> str:
    return json.dumps(
        redact_sensitive(value),
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        default=_json_default,
    )


def hash_payload(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _preview(value: Any, *, max_depth: int = 4, max_items: int = 20, max_string: int = 240) -> Any:
    value = redact_sensitive(value)
    if max_depth <= 0:
        return "<truncated>"
    if isinstance(value, Mapping):
        items = list(value.items())
        out = {
            str(k): _preview(v, max_depth=max_depth - 1, max_items=max_items, max_string=max_string)
            for k, v in items[:max_items]
        }
        if len(items) > max_items:
            out["_truncated_keys"] = len(items) - max_items
        return out
    if isinstance(value, list):
        out = [_preview(v, max_depth=max_depth - 1, max_items=max_items, max_string=max_string) for v in value[:max_items]]
        if len(value) > max_items:
            out.append({"_truncated_items": len(value) - max_items})
        return out
    if isinstance(value, str) and len(value) > max_string:
        return value[:max_string] + f"...<truncated {len(value) - max_string} chars>"
    if isinstance(value, Path):
        return str(value)
    return value


def _artifact_record(path: str | Path, project_root: Path | None = None) -> dict[str, Any]:
    artifact_path = Path(path)
    if project_root and not artifact_path.is_absolute():
        artifact_path = project_root / artifact_path
    record: dict[str, Any] = {"path": str(artifact_path)}
    try:
        resolved = artifact_path.resolve()
        record["path"] = str(resolved)
        if project_root:
            try:
                record["relative_path"] = str(resolved.relative_to(project_root.resolve()))
            except ValueError:
                record["outside_project_root"] = True
        if resolved.exists() and resolved.is_file():
            digest = hashlib.sha256()
            with resolved.open("rb") as fh:
                for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                    digest.update(chunk)
            stat = resolved.stat()
            record.update(
                {
                    "exists": True,
                    "sha256": digest.hexdigest(),
                    "size": stat.st_size,
                    "mtime": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat().replace("+00:00", "Z"),
                }
            )
        else:
            record["exists"] = False
    except Exception as exc:
        record["error"] = str(exc)
    return record


def receipt_path(project_root: Path | None = None, path: str | Path | None = None) -> Path:
    target = Path(path) if path else DEFAULT_RECEIPT_PATH
    if project_root and not target.is_absolute():
        target = project_root / target
    return target


def record_action_receipt(
    action: str,
    *,
    actor: str = "backend",
    surface: str = "web_api",
    payload: Any | None = None,
    result: Any | None = None,
    status: str = "ok",
    reason: str | None = None,
    request_meta: Mapping[str, Any] | None = None,
    artifact_paths: list[str | Path] | None = None,
    project_root: Path | None = None,
    path: str | Path | None = None,
) -> dict[str, Any]:
    contract = get_action_contract(action)
    payload_preview = _preview(payload or {})
    result_preview = _preview(result or {})
    artifacts = [_artifact_record(item, project_root=project_root) for item in (artifact_paths or [])]
    receipt = {
        "version": RECEIPT_VERSION,
        "receipt_id": f"rec_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:10]}",
        "timestamp": utc_timestamp(),
        "action": action,
        "status": status,
        "actor": actor,
        "surface": surface,
        "reason": reason,
        "contract": contract,
        "request": _preview(dict(request_meta or {}), max_depth=2),
        "payload_hash": hash_payload(payload or {}),
        "result_hash": hash_payload(result or {}),
        "payload_preview": payload_preview,
        "result_preview": result_preview,
        "artifacts": artifacts,
    }

    target = receipt_path(project_root=project_root, path=path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with _WRITE_LOCK:
        with target.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(receipt, ensure_ascii=False, sort_keys=True, default=_json_default) + "\n")
    return receipt


def safe_record_action_receipt(*args: Any, **kwargs: Any) -> dict[str, Any]:
    try:
        return record_action_receipt(*args, **kwargs)
    except Exception as exc:
        action = str(args[0]) if args else str(kwargs.get("action", "unknown"))
        return {
            "version": RECEIPT_VERSION,
            "receipt_id": None,
            "timestamp": utc_timestamp(),
            "action": action,
            "status": "receipt_error",
            "error": str(exc),
            "contract": get_action_contract(action),
        }


def receipt_response_metadata(receipt: Mapping[str, Any] | None) -> dict[str, Any]:
    if not receipt:
        return {}
    contract = receipt.get("contract") if isinstance(receipt.get("contract"), Mapping) else {}
    return {
        "receipt_id": receipt.get("receipt_id"),
        "timestamp": receipt.get("timestamp"),
        "action": receipt.get("action"),
        "status": receipt.get("status"),
        "payload_hash": receipt.get("payload_hash"),
        "result_hash": receipt.get("result_hash"),
        "markings": list(contract.get("markings", [])),
        "risk": contract.get("risk"),
        "scope": contract.get("scope"),
        "access_mode": contract.get("access_mode"),
        "artifacts": receipt.get("artifacts", []),
    }


def read_action_receipts(
    *,
    project_root: Path | None = None,
    path: str | Path | None = None,
    limit: int = 50,
    action: str | None = None,
) -> list[dict[str, Any]]:
    target = receipt_path(project_root=project_root, path=path)
    if not target.exists():
        return []
    limit = max(1, min(int(limit or 50), 500))
    rows: list[dict[str, Any]] = []
    with target.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            if action and item.get("action") != action:
                continue
            rows.append(item)
    return rows[-limit:][::-1]
