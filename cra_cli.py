#!/usr/bin/env python3
"""
SSH-friendly CLI for the Causation Research Assistant backend.

This talks to the running Flask backend on the same box, so you can use the
CRA and core monitoring endpoints without opening the browser UI.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib import error, parse, request


DEFAULT_BASE_URL = "http://127.0.0.1:5000"
DEFAULT_HF_MODEL = os.getenv("CRA_DEFAULT_HF_MODEL", "Qwen/Qwen2.5-7B-Instruct")
HF_MODEL_ALIASES = {
    "qwen": "Qwen/Qwen2.5-7B-Instruct",
    "qwen2.5": "Qwen/Qwen2.5-7B-Instruct",
    "qwen2.5-7b": "Qwen/Qwen2.5-7B-Instruct",
    "llama3.2": "meta-llama/Llama-3.2-3B-Instruct",
    "llama3.2:latest": "meta-llama/Llama-3.2-3B-Instruct",
}
NOTE_TYPES = [
    "note",
    "observation",
    "hypothesis",
    "causation",
    "analysis",
    "conclusion",
    "question",
    "todo",
    "cra",
]


class CRAClient:
    def __init__(self, base_url: str, timeout: float = 60.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def request_json(
        self,
        method: str,
        path: str,
        payload: Optional[Dict[str, Any]] = None,
        query: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        url = self._build_url(path, query=query)
        body = None
        headers = {"Accept": "application/json"}
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = request.Request(url, data=body, method=method.upper(), headers=headers)
        try:
            with request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read().decode("utf-8")
                if not raw.strip():
                    return {}
                return json.loads(raw)
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {exc.code} for {path}: {detail}") from exc
        except error.URLError as exc:
            raise RuntimeError(
                f"Could not reach CRA backend at {self.base_url}. "
                f"Is unified_entry.py or causation_web_ui.py running?"
            ) from exc

    def download(self, path: str, destination: Path) -> int:
        url = self._build_url(path)
        req = request.Request(url, headers={"Accept": "*/*"})
        try:
            with request.urlopen(req, timeout=self.timeout) as resp:
                data = resp.read()
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {exc.code} while downloading {path}: {detail}") from exc
        except error.URLError as exc:
            raise RuntimeError(
                f"Could not reach CRA backend at {self.base_url}. "
                f"Is unified_entry.py or causation_web_ui.py running?"
            ) from exc

        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        return len(data)

    def _build_url(self, path: str, query: Optional[Dict[str, Any]] = None) -> str:
        normalized_path = path if path.startswith("/") else f"/{path}"
        url = f"{self.base_url}{normalized_path}"
        if query:
            filtered = {k: v for k, v in query.items() if v is not None}
            if filtered:
                url = f"{url}?{parse.urlencode(filtered, doseq=True)}"
        return url


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="CLI for the Convergence Research Assistant backend."
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help=f"CRA backend base URL (default: {DEFAULT_BASE_URL})",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=60.0,
        help="HTTP timeout in seconds (default: 60)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print raw JSON for the selected command.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("status", help="Show CRA custodian status.")
    subparsers.add_parser("sitrep", help="Show combined operational summary.")
    subparsers.add_parser("health", help="Run CRA health check.")
    subparsers.add_parser("system", help="Show current system state snapshot.")
    subparsers.add_parser("data", help="Show full CRA data package.")
    models_parser = subparsers.add_parser(
        "models",
        help="Search public Hugging Face text-generation models.",
    )
    models_parser.add_argument("--query", "-q", default="", help="Optional Hub search text.")
    models_parser.add_argument("--limit", type=int, default=20, help="Max models to show.")
    models_parser.add_argument(
        "--pipeline",
        default="text-generation",
        help="Hugging Face pipeline tag (default: text-generation).",
    )
    subparsers.add_parser("sim-status", help="Show simulation running state.")
    subparsers.add_parser("sim-start", help="Send simulation start signal.")
    subparsers.add_parser("sim-stop", help="Send simulation stop signal.")
    subparsers.add_parser("guardian-on", help="Enable CRA guardian mode.")
    subparsers.add_parser("capsules", help="List saved organism capsules.")
    subparsers.add_parser("checkpoint-status", help="Show checkpoint health/status.")
    subparsers.add_parser("checkpoint-list", help="List available neural checkpoints.")
    subparsers.add_parser("training-status", help="Show training/checkpoint/log summary.")
    subparsers.add_parser("exporter-status", help="Show exporter pipeline readiness summary.")
    subparsers.add_parser("security-contracts", help="List action contracts and markings.")
    security_receipts_parser = subparsers.add_parser(
        "security-receipts",
        help="Show recent action/security receipts.",
    )
    security_receipts_parser.add_argument("--limit", type=int, default=20, help="Max receipts to show.")
    security_receipts_parser.add_argument("--action", help="Filter by action name.")

    events_parser = subparsers.add_parser("events", help="Show recent CRA events.")
    events_parser.add_argument("--limit", type=int, default=10, help="Max events to print.")

    logs_parser = subparsers.add_parser("logs", help="Show CRA log tails.")
    logs_parser.add_argument(
        "--log",
        help="Specific log file name to print, e.g. system.log or reality_sim.log",
    )
    logs_parser.add_argument(
        "--tail",
        type=int,
        default=20,
        help="Lines to show per log (default: 20)",
    )

    config_parser = subparsers.add_parser("config", help="Inspect CRA/runtime config data.")
    config_parser.add_argument(
        "--current",
        action="store_true",
        help="Use /api/config/current instead of /api/cra/config.",
    )
    config_parser.add_argument(
        "--history",
        action="store_true",
        help="Use /api/config/history.",
    )
    config_parser.add_argument(
        "--actions",
        action="store_true",
        help="Use /api/config/actions.",
    )
    config_parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Max config history/action entries to print.",
    )

    config_set_parser = subparsers.add_parser(
        "config-set",
        help="Apply a guarded runtime config patch through CRA config update.",
    )
    config_set_parser.add_argument("path", help="JSON pointer path, e.g. /simulation/max_steps")
    config_set_parser.add_argument("value", help="New value. JSON is accepted.")
    config_set_parser.add_argument(
        "--op",
        default="replace",
        choices=["replace", "add", "remove"],
        help="Patch operation (default: replace)",
    )
    config_set_parser.add_argument(
        "--reason",
        default="cra_cli_config_set",
        help="Reason recorded with the config action.",
    )

    config_rollback_parser = subparsers.add_parser(
        "config-rollback",
        help="Rollback recent config changes.",
    )
    config_rollback_parser.add_argument(
        "--steps",
        type=int,
        default=1,
        help="Number of history steps to roll back (default: 1)",
    )
    config_rollback_parser.add_argument(
        "--reason",
        default="cra_cli_config_rollback",
        help="Reason recorded with the rollback action.",
    )

    org_parser = subparsers.add_parser("organisms", help="List top organisms.")
    org_parser.add_argument("--limit", type=int, default=10, help="Max organisms to print.")

    alliance_parser = subparsers.add_parser("alliances", help="List alliances.")
    alliance_parser.add_argument("--limit", type=int, default=10, help="Max alliances to print.")

    chat_parser = subparsers.add_parser("chat", help="Send a single message to the CRA.")
    chat_parser.add_argument("message", nargs="*", help="Message text. Reads stdin if omitted.")
    chat_parser.add_argument("--model", default=DEFAULT_HF_MODEL, help="Hugging Face text model id.")
    chat_parser.add_argument("--vision-model", help="Optional Hugging Face vision model id.")
    chat_parser.add_argument("--api-key", help="Optional Hugging Face token override.")
    chat_parser.add_argument(
        "--inference-provider",
        help="Optional Hugging Face Inference Router provider, such as together or hf-inference.",
    )
    chat_parser.add_argument("--selected-event", help="Optional selected event id.")
    chat_parser.add_argument(
        "--view-state-file",
        help="Path to JSON file containing the frontend-style view_state object.",
    )

    butterfly_chat_parser = subparsers.add_parser(
        "butterfly-chat",
        help="Chat directly with the organism swarm through Butterfly Chat.",
    )
    butterfly_chat_parser.add_argument("message", nargs="*", help="Message text. Reads stdin if omitted.")
    butterfly_chat_parser.add_argument(
        "--routing-strategy",
        default="all",
        help="Router strategy passed to /api/butterfly/chat (default: all).",
    )
    butterfly_chat_parser.add_argument(
        "--max-organisms",
        type=int,
        default=10,
        help="Maximum organisms to query (default: 10).",
    )
    butterfly_chat_parser.add_argument(
        "--min-mastery-level",
        type=int,
        default=0,
        help="Only include organisms at or above this mastery level (default: 0).",
    )

    standin_chat_parser = subparsers.add_parser(
        "standin-chat",
        help="Provider-free CRA stand-in: chat directly with Butterfly Chat without Ollama.",
    )
    standin_chat_parser.add_argument("message", nargs="*", help="Message text. Reads stdin if omitted.")
    standin_chat_parser.add_argument(
        "--routing-strategy",
        default="all",
        help="Router strategy passed to /api/butterfly/chat (default: all).",
    )
    standin_chat_parser.add_argument(
        "--max-organisms",
        type=int,
        default=10,
        help="Maximum organisms to query (default: 10).",
    )
    standin_chat_parser.add_argument(
        "--min-mastery-level",
        type=int,
        default=0,
        help="Only include organisms at or above this mastery level (default: 0).",
    )

    organism_chat_parser = subparsers.add_parser(
        "organism-chat",
        help="Chat directly with one organism by id.",
    )
    organism_chat_parser.add_argument("organism_id", help="Target organism id.")
    organism_chat_parser.add_argument("message", nargs="*", help="Message text. Reads stdin if omitted.")

    subparsers.add_parser(
        "swarm-stats",
        help="Show Butterfly Chat language-learning and training stats.",
    )

    notepad_parser = subparsers.add_parser(
        "notepad",
        help="Read/search the CRA Research Notepad scientific journal.",
    )
    notepad_parser.add_argument("--type", choices=NOTE_TYPES, help="Filter by note type.")
    notepad_parser.add_argument("--query", help="Search content, tags, and linked events.")
    notepad_parser.add_argument("--limit", type=int, default=20, help="Max entries to show.")
    notepad_parser.add_argument("--summary", action="store_true", help="Show summary only.")

    notepad_add_parser = subparsers.add_parser(
        "notepad-add",
        help="Append an entry to the CRA Research Notepad.",
    )
    notepad_add_parser.add_argument("type", choices=NOTE_TYPES, help="Entry type.")
    notepad_add_parser.add_argument("message", nargs="*", help="Entry content. Reads stdin if omitted.")
    notepad_add_parser.add_argument("--event", action="append", default=[], help="Linked event id. Repeat as needed.")
    notepad_add_parser.add_argument("--confidence", choices=["low", "medium", "high"], help="Hypothesis confidence.")
    notepad_add_parser.add_argument("--cause", help="Cause event id for causation notes.")
    notepad_add_parser.add_argument("--effect", help="Effect event id for causation notes.")
    notepad_add_parser.add_argument("--source", default="cra_cli", help="Source metadata label.")

    cocoon_validate_parser = subparsers.add_parser(
        "cocoon-validate",
        help="Validate a Cocoon ZIP or extracted package without starting the main system.",
    )
    cocoon_validate_parser.add_argument("path", help="Path to Cocoon ZIP or extracted directory.")
    cocoon_validate_parser.add_argument(
        "--run-info",
        action="store_true",
        help="Run cocoon.py --mode info --max-organisms 1 after extraction/directory check.",
    )
    cocoon_validate_parser.add_argument(
        "--python",
        default=sys.executable,
        help="Python executable for --run-info (default: current interpreter).",
    )

    receipt_parser = subparsers.add_parser(
        "scientific-receipt",
        help="Capture a CRA scientific run receipt into the Research Notepad.",
    )
    receipt_parser.add_argument(
        "--title",
        default="Scientific run receipt",
        help="Receipt title/content prefix.",
    )
    receipt_parser.add_argument(
        "--tag",
        default="#scientific_receipt",
        help="Hashtag to include in the notepad entry.",
    )
    receipt_parser.add_argument(
        "--event-limit",
        type=int,
        default=5,
        help="Recent event count to include.",
    )

    repl_parser = subparsers.add_parser(
        "repl",
        help="Interactive CRA shell over SSH. Type /help for local commands.",
    )
    repl_parser.add_argument("--model", default=DEFAULT_HF_MODEL, help="Hugging Face text model id.")
    repl_parser.add_argument("--vision-model", help="Optional Hugging Face vision model id.")
    repl_parser.add_argument("--api-key", help="Optional Hugging Face token override.")
    repl_parser.add_argument(
        "--inference-provider",
        help="Optional Hugging Face Inference Router provider, such as together or hf-inference.",
    )

    compile_org_parser = subparsers.add_parser(
        "compile-organism",
        help="Compile a single organism to an export archive and save it locally.",
    )
    compile_org_parser.add_argument("organism_id", help="Organism id to compile.")
    compile_org_parser.add_argument(
        "--format",
        default="onnx",
        choices=["onnx", "torchscript"],
        help="Export format (default: onnx)",
    )
    compile_org_parser.add_argument(
        "--outdir",
        default="agent_downloads",
        help="Directory to save downloaded artifacts.",
    )

    compile_ensemble_parser = subparsers.add_parser(
        "compile-ensemble",
        help="Compile multiple organisms into a single ensemble archive.",
    )
    compile_ensemble_parser.add_argument(
        "organism_ids",
        nargs="+",
        help="One or more organism ids.",
    )
    compile_ensemble_parser.add_argument(
        "--format",
        default="onnx",
        choices=["onnx", "torchscript"],
        help="Export format (default: onnx)",
    )
    compile_ensemble_parser.add_argument(
        "--outdir",
        default="agent_downloads",
        help="Directory to save downloaded artifacts.",
    )

    compile_learning_parser = subparsers.add_parser(
        "compile-learning",
        help="Compile a trainable learning capsule archive.",
    )
    compile_learning_parser.add_argument(
        "--organism-id",
        dest="organism_ids",
        action="append",
        default=[],
        help="Organism id to include. Repeat for multiple organisms.",
    )
    compile_learning_parser.add_argument(
        "--training-config-file",
        help="Path to JSON file with training_config overrides.",
    )
    compile_learning_parser.add_argument(
        "--outdir",
        default="agent_downloads",
        help="Directory to save downloaded artifacts.",
    )

    compile_cocoon_parser = subparsers.add_parser(
        "compile-cocoon",
        help="Compile a cocoon/package export and save it locally.",
    )
    compile_cocoon_parser.add_argument(
        "--organism-id",
        dest="organism_ids",
        action="append",
        default=[],
        help="Organism id to include. Repeat for multiple organisms.",
    )
    compile_cocoon_parser.add_argument(
        "--top-n",
        type=int,
        default=1,
        help="Use top N organisms if no --organism-id values are provided.",
    )
    compile_cocoon_parser.add_argument(
        "--alliance-id",
        dest="alliance_ids",
        action="append",
        default=[],
        help="Alliance id to include in a curated Cocoon. Repeat for 2-3 alliances.",
    )
    compile_cocoon_parser.add_argument(
        "--alliance",
        dest="alliance_names",
        action="append",
        default=[],
        help="Alliance name or id to include in a curated Cocoon.",
    )
    compile_cocoon_parser.add_argument(
        "--include-unallied",
        action="store_true",
        help="Include organisms with no alliance mapping. Default excludes them.",
    )
    compile_cocoon_parser.add_argument(
        "--format",
        default="cocoon",
        choices=["cocoon", "onnx", "torchscript", "package"],
        help="Export format (default: cocoon)",
    )
    compile_cocoon_parser.add_argument(
        "--no-gym",
        action="store_true",
        help="Disable gym adapter in export.",
    )
    compile_cocoon_parser.add_argument(
        "--no-http",
        action="store_true",
        help="Disable HTTP server in export.",
    )
    compile_cocoon_parser.add_argument(
        "--no-compress",
        action="store_true",
        help="Disable export compression.",
    )
    compile_cocoon_parser.add_argument(
        "--outdir",
        default="agent_downloads",
        help="Directory to save downloaded artifacts.",
    )
    compile_cocoon_parser.add_argument(
        "--reason",
        default="cra_cli_compile_cocoon",
        help="Reason recorded with the cocoon compile receipt.",
    )

    checkpoint_save_parser = subparsers.add_parser(
        "checkpoint-save",
        help="Trigger an immediate neural checkpoint save.",
    )
    checkpoint_save_parser.add_argument(
        "--reason",
        default="cra_cli_manual_save",
        help="Reason recorded in the checkpoint signal.",
    )

    checkpoint_restore_parser = subparsers.add_parser(
        "checkpoint-restore",
        help="Signal restore from a checkpoint (applies on next start/restart).",
    )
    checkpoint_restore_parser.add_argument(
        "--name",
        help="Checkpoint directory name. Defaults to latest if omitted.",
    )
    checkpoint_restore_parser.add_argument(
        "--reason",
        default="cra_cli_checkpoint_restore",
        help="Reason recorded with the restore receipt.",
    )

    api_parser = subparsers.add_parser(
        "api",
        help="Call any CRA/web API route directly.",
    )
    api_parser.add_argument("path", help="API path, e.g. /api/cra/status")
    api_parser.add_argument(
        "--method",
        default="GET",
        choices=["GET", "POST"],
        help="HTTP method (default: GET)",
    )
    api_parser.add_argument(
        "--data",
        help="JSON body for POST requests.",
    )
    api_parser.add_argument(
        "--query",
        action="append",
        default=[],
        help="Query pair in key=value form. Repeat as needed.",
    )

    return parser.parse_args()


def read_message(args: argparse.Namespace) -> str:
    if args.message:
        return " ".join(args.message).strip()
    if not sys.stdin.isatty():
        return sys.stdin.read().strip()
    raise SystemExit("Message is required. Pass it as arguments or pipe it on stdin.")


def read_view_state(path: Optional[str]) -> Dict[str, Any]:
    if not path:
        return {}
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def read_json_file(path: Optional[str]) -> Dict[str, Any]:
    if not path:
        return {}
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def print_json(data: Any) -> None:
    print(json.dumps(data, indent=2, sort_keys=False))


def print_heading(title: str) -> None:
    print(f"\n== {title} ==")


def format_timestamp(value: Any) -> str:
    return str(value) if value is not None else "-"


def summarize_status(data: Dict[str, Any]) -> None:
    custodian = data.get("custodian", {})
    monitoring = custodian.get("monitoring", {})
    print(f"Role: {custodian.get('role', '-')}")
    print(f"Status: {custodian.get('status', '-')}")
    print(f"Protection: {custodian.get('protection_status', '-')}")
    print(f"Event streaming: {monitoring.get('event_streaming', False)}")
    print(f"WebSocket support: {monitoring.get('websocket_support', False)}")
    capabilities = custodian.get("capabilities", [])
    if capabilities:
        print("Capabilities:")
        for item in capabilities:
            print(f"  - {item}")


def summarize_health(data: Dict[str, Any]) -> None:
    print(f"Overall health: {data.get('overall_health', '-')}")
    for key in ("critical_issues", "warnings", "recommendations"):
        items = data.get(key, [])
        if items:
            print(f"{key.replace('_', ' ').title()}:")
            for item in items:
                print(f"  - {item}")


def summarize_sitrep(
    status_data: Dict[str, Any],
    health_data: Dict[str, Any],
    system_data: Dict[str, Any],
    checkpoint_data: Dict[str, Any],
) -> None:
    print_heading("CRA")
    summarize_status(status_data)
    print_heading("Health")
    summarize_health(health_data)
    print_heading("System")
    summarize_system(system_data)
    print_heading("Training")
    summarize_checkpoints(checkpoint_data)


def summarize_system(data: Dict[str, Any]) -> None:
    state = data.get("state", {})
    sim = state.get("simulation", {})
    pc = state.get("pc_resources", {})
    memory = pc.get("memory", {})
    cpu = pc.get("cpu", {})
    butterfly = state.get("butterfly_system", {})

    print(f"Simulation running: {sim.get('running', False)}")
    print(f"Paused: {sim.get('paused', True)}")
    print(f"Frame: {sim.get('frame', 0)}")
    print(f"FPS: {sim.get('fps', 0.0)}")
    print(f"CPU total: {cpu.get('total_percent', 0):.1f}%")
    print(f"Memory used: {memory.get('used_gb', 0):.2f} / {memory.get('total_gb', 0):.2f} GB")
    print(f"Process RSS: {memory.get('process_mb', 0):.1f} MB")
    print(f"Nodes: {butterfly.get('total_nodes', 0)}")
    print(f"Links: {butterfly.get('total_links', 0)}")
    warnings = state.get("warnings", [])
    if warnings:
        print("Warnings:")
        for item in warnings:
            print(f"  - {item}")


def summarize_models(data: Dict[str, Any]) -> None:
    text_models = data.get("text_models") or data.get("models") or []
    vision_models = data.get("vision_models") or []
    heading = "Hugging Face models" if data.get("pipeline") or data.get("query") is not None else "Text models"
    print(f"{heading}:")
    for item in text_models:
        if isinstance(item, dict):
            model_id = item.get("id") or item.get("modelId") or "-"
            details = []
            if item.get("pipeline_tag"):
                details.append(str(item["pipeline_tag"]))
            if item.get("downloads") is not None:
                details.append(f"downloads={item['downloads']}")
            if item.get("likes") is not None:
                details.append(f"likes={item['likes']}")
            suffix = f" ({', '.join(details)})" if details else ""
            print(f"  - {model_id}{suffix}")
        else:
            print(f"  - {item}")
    if vision_models:
        print("Vision models:")
        for item in vision_models:
            print(f"  - {item}")


def summarize_sim_status(data: Dict[str, Any]) -> None:
    print(f"Running: {data.get('running', False)}")
    print(f"Paused: {data.get('paused', True)}")
    if "message" in data:
        print(data["message"])


def summarize_events(data: Dict[str, Any], limit: int) -> None:
    events = data.get("events", [])[:limit]
    print(f"Events shown: {len(events)}")
    for idx, event in enumerate(events, start=1):
        etype = event.get("type") or event.get("event_type") or "unknown"
        timestamp = format_timestamp(event.get("timestamp"))
        print(f"{idx}. {etype} @ {timestamp}")
        summary = event.get("data") or event.get("message") or event.get("payload")
        if summary:
            if isinstance(summary, dict):
                summary = json.dumps(summary, ensure_ascii=True)
            print(f"   {str(summary)[:220]}")


def summarize_logs(data: Dict[str, Any], log_name: Optional[str], tail: int) -> None:
    logs = data.get("logs", {})
    if log_name:
        selected = logs.get(log_name)
        if not selected:
            raise SystemExit(f"Log {log_name!r} not found. Available: {', '.join(sorted(logs))}")
        content = selected.get("content", [])
        for line in content[-tail:]:
            print(line)
        return

    for name in sorted(logs):
        payload = logs[name]
        print_heading(name)
        print(f"Entries loaded: {payload.get('entries', 0)}")
        for line in payload.get("content", [])[-tail:]:
            print(line)


def summarize_config(data: Dict[str, Any], limit: int) -> None:
    if "history" in data:
        entries = data.get("history", [])[-limit:]
        print(f"History entries shown: {len(entries)}")
        for idx, entry in enumerate(entries, start=1):
            print(
                f"{idx}. version={entry.get('version', '-')} "
                f"timestamp={format_timestamp(entry.get('timestamp'))}"
            )
    elif "actions" in data:
        entries = data.get("actions", [])[-limit:]
        print(f"Actions shown: {len(entries)}")
        for idx, entry in enumerate(entries, start=1):
            print(
                f"{idx}. {entry.get('action', '-')} path={entry.get('path', '-')} "
                f"actor={entry.get('actor', '-')} status={entry.get('status', '-')}"
            )
    elif "config" in data and isinstance(data["config"], dict):
        keys = ", ".join(sorted(data["config"].keys()))
        print(f"Config payload keys: {keys}")
        print_json(data["config"])
    else:
        print_json(data)


def summarize_organisms(data: List[Dict[str, Any]], limit: int) -> None:
    shown = data[:limit]
    print(f"Organisms shown: {len(shown)}")
    for idx, org in enumerate(shown, start=1):
        print(
            f"{idx}. id={org.get('id', '-')[:12]} "
            f"fitness={org.get('fitness', 0):.4f} "
            f"words={org.get('words_learned', 0)} "
            f"personality={org.get('personality_type', '-')}"
        )


def summarize_alliances(data: List[Dict[str, Any]], limit: int) -> None:
    shown = data[:limit]
    print(f"Alliances shown: {len(shown)}")
    for idx, alliance in enumerate(shown, start=1):
        print(
            f"{idx}. {alliance.get('name', alliance.get('alliance_id', '-'))} "
            f"members={alliance.get('member_count', len(alliance.get('members', [])))} "
            f"fitness={alliance.get('collective_fitness', alliance.get('average_fitness', 0))}"
        )


def summarize_capsules(data: Dict[str, Any]) -> None:
    capsules = data.get("capsules", [])
    print(f"Capsules: {len(capsules)}")
    for idx, capsule in enumerate(capsules[:20], start=1):
        print(
            f"{idx}. organism={capsule.get('organism_id', '-')[:12]} "
            f"capsule={capsule.get('capsule_id', '-')[:12]} "
            f"fitness={capsule.get('fitness', 0)} "
            f"captured={format_timestamp(capsule.get('capture_time'))}"
        )


def summarize_checkpoints(data: Dict[str, Any]) -> None:
    if "checkpoint_status" in data:
        status = data.get("checkpoint_status", {})
        health = status.get("health", {})
        print(f"Enabled: {status.get('enabled', False)}")
        print(f"Count: {status.get('checkpoints_count', 0)}")
        print(f"Total size MB: {status.get('total_size_mb', 0)}")
        latest = status.get("latest_checkpoint") or {}
        if latest:
            print(
                f"Latest: {latest.get('name', '-')} "
                f"gen={latest.get('generation', '-')} "
                f"timestamp={format_timestamp(latest.get('timestamp'))}"
            )
        if health.get("recommendation"):
            print(f"Recommendation: {health['recommendation']}")
        return

    checkpoints = data.get("checkpoints", [])
    print(f"Checkpoints: {len(checkpoints)}")
    for idx, checkpoint in enumerate(checkpoints[:20], start=1):
        print(
            f"{idx}. {checkpoint.get('name', '-')} "
            f"gen={checkpoint.get('generation', '-')} "
            f"size={checkpoint.get('size_mb', 0)}MB "
            f"timestamp={format_timestamp(checkpoint.get('timestamp'))}"
        )


def summarize_training_status(
    system_data: Dict[str, Any],
    checkpoint_data: Dict[str, Any],
    logs_data: Dict[str, Any],
) -> None:
    summarize_system(system_data)
    print_heading("Checkpointing")
    summarize_checkpoints(checkpoint_data)
    print_heading("Neural Log")
    neural_log = logs_data.get("logs", {}).get("neural.log", {})
    for line in neural_log.get("content", [])[-15:]:
        print(line)


def summarize_exporter_status(
    organisms_data: List[Dict[str, Any]],
    capsules_data: Dict[str, Any],
    checkpoint_data: Dict[str, Any],
) -> None:
    print(f"Live/saved organisms visible to exporter: {len(organisms_data)}")
    if organisms_data:
        print("Top organisms:")
        for idx, org in enumerate(organisms_data[:5], start=1):
            print(
                f"  {idx}. id={org.get('id', '-')[:12]} "
                f"fitness={org.get('fitness', 0):.4f} "
                f"source={org.get('source', '-')}"
            )
    capsules = capsules_data.get("capsules", [])
    print(f"Saved capsules: {len(capsules)}")
    latest_capsules = sorted(
        capsules,
        key=lambda item: str(item.get("capture_time") or ""),
        reverse=True,
    )[:5]
    if latest_capsules:
        print("Recent capsules:")
        for idx, capsule in enumerate(latest_capsules, start=1):
            print(
                f"  {idx}. organism={str(capsule.get('organism_id', '-'))[:12]} "
                f"captured={format_timestamp(capsule.get('capture_time'))} "
                f"reason={capsule.get('reason', '-')}"
            )
    print_heading("Checkpointing")
    summarize_checkpoints(checkpoint_data)


def save_downloads(client: CRAClient, data: Dict[str, Any], outdir: str) -> List[Path]:
    saved: List[Path] = []
    target_dir = Path(outdir)
    filename = data.get("filename")
    download_url = data.get("download_url")
    if filename and download_url:
        destination = target_dir / filename
        client.download(download_url, destination)
        saved.append(destination)

    for extra in data.get("additional_files", []) or []:
        extra_name = extra.get("filename")
        extra_url = extra.get("download_url")
        if extra_name and extra_url:
            destination = target_dir / extra_name
            client.download(extra_url, destination)
            saved.append(destination)

    return saved


def summarize_export_result(data: Dict[str, Any], saved_paths: List[Path]) -> None:
    print(f"Success: {data.get('success', False)}")
    if data.get("capsule_type"):
        print(f"Capsule type: {data.get('capsule_type')}")
    if data.get("export_format"):
        print(f"Format: {data.get('export_format')}")
    if data.get("mode"):
        print(f"Mode: {data.get('mode')}")
    if data.get("organism_count") is not None:
        print(f"Organisms: {data.get('organism_count')}")
    if data.get("size") is not None:
        print(f"Size: {data.get('size')} bytes")
    if data.get("usage_hint"):
        print(f"Usage: {data.get('usage_hint')}")
    if saved_paths:
        print("Saved:")
        for path in saved_paths:
            print(f"  - {path}")


def parse_jsonish_value(raw: str) -> Any:
    text = raw.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        lowered = text.lower()
        if lowered == "true":
            return True
        if lowered == "false":
            return False
        if lowered == "null":
            return None
        return raw


def normalize_hf_model_id(model: Optional[str]) -> str:
    raw = (model or DEFAULT_HF_MODEL).strip()
    if not raw:
        return DEFAULT_HF_MODEL
    return HF_MODEL_ALIASES.get(raw.lower(), raw)


def resolve_hf_token(api_key: Optional[str]) -> Optional[str]:
    return api_key or os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_API_KEY")


def do_chat(
    client: CRAClient,
    message: str,
    model: str,
    vision_model: Optional[str] = None,
    api_key: Optional[str] = None,
    selected_event: Optional[str] = None,
    view_state: Optional[Dict[str, Any]] = None,
    inference_provider: Optional[str] = None,
) -> Dict[str, Any]:
    resolved_token = resolve_hf_token(api_key)
    payload: Dict[str, Any] = {
        "message": message,
        "model": normalize_hf_model_id(model),
        "provider": "huggingface",
        "view_state": view_state or {},
    }
    if vision_model:
        payload["vision_model"] = normalize_hf_model_id(vision_model)
    if resolved_token:
        payload["api_key"] = resolved_token
        payload["hf_api_key"] = resolved_token
    if inference_provider:
        payload["inference_provider"] = inference_provider
    if selected_event:
        payload["selected_event"] = selected_event
    return client.request_json("POST", "/api/cra/chat", payload=payload)


def summarize_chat(data: Dict[str, Any]) -> None:
    response = data.get("response") or data.get("message") or ""
    if response:
        print(response.strip())
    if not response:
        print_json(data)
        return

    timing = data.get("timing_breakdown") or data.get("timing") or {}
    if timing:
        print_heading("Timing")
        print_json(timing)
    if data.get("vision_analysis"):
        print_heading("Vision")
        print(data["vision_analysis"])


def butterfly_chat_failed(data: Dict[str, Any]) -> bool:
    routing = data.get("routing_info") or {}
    responded = routing.get("organisms_responded", data.get("organism_count", 0))
    try:
        organisms_responded = int(responded or 0)
    except (TypeError, ValueError):
        organisms_responded = 0

    response = str(data.get("response") or "").strip()
    if response == "<no response>":
        response = ""

    return (
        data.get("success") is False
        or data.get("status") == "error"
        or organisms_responded == 0
        or not response
    )


def summarize_butterfly_chat(data: Dict[str, Any]) -> None:
    response = data.get("response") or ""
    failed = butterfly_chat_failed(data)
    printed_response = False
    if failed:
        print_heading("Butterfly Chat Failed")
        reason = data.get("failure_reason") or data.get("status") or "unknown_failure"
        print(f"Reason: {reason}")
        routing = data.get("routing_info") or {}
        if routing:
            print(f"Organisms queried: {routing.get('organisms_queried', 0)}")
            print(f"Organisms responded: {routing.get('organisms_responded', 0)}")
        if response.strip():
            print(response.strip())
            printed_response = True

    if response:
        if not printed_response:
            print(response.strip())
    else:
        print_json(data)
        return

    print_heading("Swarm")
    print(f"Organisms: {data.get('organism_count', 0)}")
    print(f"Confidence: {data.get('confidence', 0):.3f}")
    print(f"Strategy: {data.get('routing_strategy', '-')}")
    routing = data.get("routing_info") or {}
    if routing:
        selected = routing.get("selected_organisms") or routing.get("organisms") or []
        if selected:
            print(f"Selected: {len(selected)}")

    responses = data.get("organism_responses") or []
    if responses:
        print_heading("Organism Responses")
        for idx, item in enumerate(responses[:8], start=1):
            oid = str(item.get("organism_id") or item.get("id") or item.get("species_id") or "-")
            confidence = item.get("confidence", 0)
            text = item.get("response") or item.get("message") or ""
            print(f"{idx}. {oid[:12]} confidence={confidence:.3f}")
            if text:
                print(f"   {text[:220]}")

    errors = data.get("errors") or []
    if errors:
        print_heading("Errors")
        for item in errors[:5]:
            print(f"  - {item}")


def summarize_organism_chat(data: Dict[str, Any]) -> None:
    if not data.get("success", False) and "response" not in data:
        print_json(data)
        return

    print(f"Organism: {data.get('organism_id', '-')}")
    info = data.get("organism_info") or {}
    if info:
        print(
            f"Generation: {info.get('generation', 0)} "
            f"Fitness: {info.get('fitness', 0)} "
            f"Words: {info.get('vocabulary_size', 0)} "
            f"Personality: {info.get('personality', '-')}"
        )

    response = data.get("response") or ""
    if response:
        print_heading("Response")
        print(response.strip())
    print(f"Confidence: {data.get('confidence', 0):.3f}")

    debug = data.get("debug") or {}
    if debug:
        print_heading("Learning")
        print(f"Experience buffer: {debug.get('organism_experience_count', '-')}")
        print(f"Personal vocab: {debug.get('organism_personal_vocab_size', '-')}")
        print(f"Mastery atoms used: {debug.get('atoms_found_for_response', '-')}")
        atom_details = debug.get("atom_formation_details") or []
        for atom in atom_details[:8]:
            print(
                f"  - {atom.get('word', '-')} "
                f"strength={atom.get('strength', '-')} "
                f"uses={atom.get('usage_count', '-')} "
                f"source={atom.get('source', '-')}"
            )

    trail = data.get("causation_trail") or []
    if trail:
        print_heading("Causation Trail")
        for item in trail[:8]:
            print(f"  - {item}")


def summarize_swarm_stats(data: Dict[str, Any]) -> None:
    payload = data.get("agent_swarm") or data
    stats = payload.get("stats") or payload
    if not isinstance(stats, dict):
        print_json(data)
        return

    population = stats.get("population_stats") or {}
    semantic = stats.get("semantic_reward_stats") or {}
    transfer = stats.get("knowledge_transfer_stats") or {}
    vocab = stats.get("creative_vocab_stats") or {}
    derived = payload.get("derived_metrics") or data.get("derived_metrics") or {}

    print_heading("Population")
    print(f"Organisms: {population.get('total_organisms', 0)}")
    print(f"With language: {population.get('organisms_with_language', 0)}")
    print(f"Chat experiences: {population.get('total_chat_experiences', 0)}")
    print(f"Chat training triggered: {population.get('chat_training_triggered', 0)}")
    if derived:
        print(f"Training ratio: {derived.get('training_ratio', 0):.3f}")
        print(f"Learning health: {derived.get('learning_health_score', 0):.3f}")

    print_heading("Semantic Reward")
    print(f"Calculations: {semantic.get('total_calculations', 0)}")
    print(f"Average reward: {semantic.get('avg_total_reward', 0):.3f}")
    print(f"Average coherence: {semantic.get('avg_coherence', 0):.3f}")

    print_heading("Knowledge Transfer")
    print(f"Broadcasts: {transfer.get('total_broadcasts', 0)}")
    print(f"Recipients: {transfer.get('total_recipients', 0)}")
    print(f"Reward transferred: {transfer.get('total_reward_transferred', 0):.3f}")

    if vocab:
        print_heading("Vocabulary")
        print(f"Expansions: {vocab.get('total_expansions', 0)}")
        print(f"Phrases: {vocab.get('phrases_generated', 0)}")
        print(f"Compounds: {vocab.get('compounds_created', 0)}")
        print(f"Neologisms: {vocab.get('neologisms_minted', 0)}")


def summarize_notepad(data: Dict[str, Any], summary_only: bool = False) -> None:
    if not data.get("success", True):
        print_json(data)
        return

    summary = data.get("summary") or {}
    if "summary" in summary:
        summary = summary["summary"]
    entries = data.get("entries") or []

    print_heading("Research Notepad")
    print(f"Session: {data.get('sessionId', '-')}")
    print(f"Last saved: {data.get('lastSaved', '-')}")
    print(f"Total: {summary.get('total', data.get('totalEntries', len(entries)))}")
    print(f"Returned: {data.get('returned', len(entries))}")
    print(f"Open hypotheses: {summary.get('openHypotheses', 0)}")
    print(f"Pending todos: {summary.get('pendingTodos', 0)}")

    by_type = summary.get("byType") or {}
    if by_type:
        compact = ", ".join(f"{k}={v}" for k, v in sorted(by_type.items()) if v)
        if compact:
            print(f"By type: {compact}")

    if summary_only:
        return

    for entry in entries:
        timestamp = entry.get("timestamp", "-")
        note_type = entry.get("type", "note")
        content = (entry.get("content") or "").strip()
        print_heading(f"{note_type} {entry.get('id', '-')}")
        print(f"Time: {timestamp}")
        if entry.get("linkedEvents"):
            print(f"Events: {', '.join(str(e) for e in entry.get('linkedEvents', []))}")
        metadata = entry.get("metadata") or {}
        if metadata:
            useful = {k: v for k, v in metadata.items() if v not in (None, "", [])}
            if useful:
                print(f"Metadata: {json.dumps(useful, ensure_ascii=False)}")
        print(content)


def _read_zip_json(zf: zipfile.ZipFile, name: str) -> Optional[Dict[str, Any]]:
    try:
        with zf.open(name) as fh:
            data = json.loads(fh.read().decode("utf-8", errors="replace"))
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def _vocab_word_count(vocab: Optional[Dict[str, Any]]) -> int:
    if not isinstance(vocab, dict):
        return 0
    word_to_id = vocab.get("word_to_id")
    return len(word_to_id) if isinstance(word_to_id, dict) else len(vocab)


def validate_cocoon_package(path: Path, run_info: bool = False, python_executable: str = sys.executable) -> Dict[str, Any]:
    """Static validation for Cocoon ZIPs/directories used by Council adapters."""
    connector_words = {"a", "and", "to", "of", "in", "it", "is", "but", "then", "cocoon"}
    curriculum_files = {
        "curriculum/connector_words.json",
        "curriculum/dialogue_frames.json",
        "curriculum/role_transform_tasks.json",
        "curriculum/game_language_tasks.json",
        "curriculum/reward_rubric.json",
        "training_logs/schema.json",
    }
    result: Dict[str, Any] = {
        "path": str(path),
        "exists": path.exists(),
        "kind": "missing",
        "ok": False,
        "errors": [],
        "warnings": [],
        "files": {},
    }
    if not path.exists():
        result["errors"].append("Path does not exist.")
        return result

    extracted_dir: Optional[Path] = None
    temp_dir: Optional[tempfile.TemporaryDirectory[str]] = None

    try:
        if path.is_file() and path.suffix.lower() == ".zip":
            result["kind"] = "zip"
            with zipfile.ZipFile(path) as zf:
                names = [item.filename for item in zf.infolist()]
                duplicates = sorted({name for name in names if names.count(name) > 1})
                result["duplicates"] = duplicates
                if duplicates:
                    result["warnings"].append(f"Duplicate ZIP entries: {', '.join(duplicates)}")

                required = ["cocoon.py", "metadata.json", "vocabulary.json", "README.md"]
                result["files"] = {name: name in names for name in required}
                for name, present in result["files"].items():
                    if not present:
                        result["errors"].append(f"Missing {name}")

                metadata = _read_zip_json(zf, "metadata.json")
                vocab = _read_zip_json(zf, "vocabulary.json")
                readme = ""
                try:
                    readme = zf.read("README.md").decode("utf-8", errors="replace")
                except Exception:
                    pass
                result["metadata_package_version"] = metadata.get("package_version") if metadata else None
                result["metadata_vocab_size"] = metadata.get("vocab_size") if metadata else None
                result["vocabulary_count"] = _vocab_word_count(vocab)
                result["connector_words"] = {
                    word: bool(isinstance(vocab, dict) and word in (vocab.get("word_to_id") or {}))
                    for word in sorted(connector_words)
                }
                missing_connectors = [w for w, present in result["connector_words"].items() if not present]
                if missing_connectors:
                    result["warnings"].append(f"Missing connector words: {', '.join(missing_connectors)}")
                if "brain_ensemble.onnx" in readme and "brain_ensemble.onnx" not in names:
                    result["warnings"].append("README references brain_ensemble.onnx but package does not include it.")
                if "game_contracts.json" not in names:
                    result["warnings"].append("Missing game_contracts.json Council contract.")
                result["curriculum_files"] = {
                    name: name in names
                    for name in sorted(curriculum_files)
                }
                missing_curriculum = [name for name, present in result["curriculum_files"].items() if not present]
                if missing_curriculum:
                    result["warnings"].append(f"Missing language curriculum files: {', '.join(missing_curriculum)}")
                result["has_torchscript"] = "brain_ensemble.pt" in names
                result["has_onnx"] = "brain_ensemble.onnx" in names

                if run_info:
                    temp_parent = Path(os.environ.get("TEMP", tempfile.gettempdir()))
                    if Path("D:/temp").exists():
                        temp_parent = Path("D:/temp")
                    temp_dir = tempfile.TemporaryDirectory(prefix="cocoon_validate_", dir=str(temp_parent))
                    zf.extractall(temp_dir.name)
                    extracted_dir = Path(temp_dir.name)

        elif path.is_dir():
            result["kind"] = "directory"
            names = {str(p.relative_to(path)).replace("\\", "/") for p in path.rglob("*") if p.is_file()}
            required = ["cocoon.py", "metadata.json", "vocabulary.json", "README.md"]
            result["files"] = {name: name in names for name in required}
            for name, present in result["files"].items():
                if not present:
                    result["errors"].append(f"Missing {name}")
            metadata = read_json_file(str(path / "metadata.json")) if (path / "metadata.json").exists() else None
            vocab = read_json_file(str(path / "vocabulary.json")) if (path / "vocabulary.json").exists() else None
            result["metadata_package_version"] = metadata.get("package_version") if metadata else None
            result["metadata_vocab_size"] = metadata.get("vocab_size") if metadata else None
            result["vocabulary_count"] = _vocab_word_count(vocab)
            result["connector_words"] = {
                word: bool(isinstance(vocab, dict) and word in (vocab.get("word_to_id") or {}))
                for word in sorted(connector_words)
            }
            missing_connectors = [w for w, present in result["connector_words"].items() if not present]
            if missing_connectors:
                result["warnings"].append(f"Missing connector words: {', '.join(missing_connectors)}")
            if "game_contracts.json" not in names:
                result["warnings"].append("Missing game_contracts.json Council contract.")
            result["curriculum_files"] = {
                name: name in names
                for name in sorted(curriculum_files)
            }
            missing_curriculum = [name for name, present in result["curriculum_files"].items() if not present]
            if missing_curriculum:
                result["warnings"].append(f"Missing language curriculum files: {', '.join(missing_curriculum)}")
            result["has_torchscript"] = "brain_ensemble.pt" in names
            result["has_onnx"] = "brain_ensemble.onnx" in names
            extracted_dir = path
        else:
            result["errors"].append("Path must be a Cocoon ZIP or extracted directory.")

        if run_info and extracted_dir:
            cocoon_py = extracted_dir / "cocoon.py"
            if cocoon_py.exists():
                proc = subprocess.run(
                    [python_executable, str(cocoon_py), "--mode", "info", "--max-organisms", "1"],
                    cwd=str(extracted_dir),
                    capture_output=True,
                    text=True,
                    timeout=90,
                    env={**os.environ, "PYTHONIOENCODING": "utf-8"},
                )
                result["runtime_info"] = {
                    "returncode": proc.returncode,
                    "stdout_tail": proc.stdout[-4000:],
                    "stderr_tail": proc.stderr[-2000:],
                }
                if proc.returncode != 0:
                    result["warnings"].append("cocoon.py --mode info returned nonzero.")
            else:
                result["warnings"].append("Cannot run info: cocoon.py missing.")
    finally:
        if temp_dir is not None:
            temp_dir.cleanup()

    result["ok"] = not result["errors"]
    return result


def summarize_cocoon_validation(data: Dict[str, Any]) -> None:
    print_heading("Cocoon Validation")
    print(f"Path: {data.get('path')}")
    print(f"Kind: {data.get('kind')}")
    print(f"OK: {data.get('ok')}")
    print(f"Vocab count: {data.get('vocabulary_count', 0)}")
    print(f"Metadata vocab: {data.get('metadata_vocab_size', '-')}")
    print(f"TorchScript: {data.get('has_torchscript', False)}")
    print(f"ONNX: {data.get('has_onnx', False)}")
    connectors = data.get("connector_words") or {}
    if connectors:
        missing = [word for word, present in connectors.items() if not present]
        print(f"Connectors missing: {', '.join(missing) if missing else 'none'}")
    curriculum = data.get("curriculum_files") or {}
    if curriculum:
        missing = [name for name, present in curriculum.items() if not present]
        print(f"Curriculum files missing: {', '.join(missing) if missing else 'none'}")
    for key in ("errors", "warnings"):
        items = data.get(key) or []
        if items:
            print_heading(key.title())
            for item in items:
                print(f"- {item}")
    runtime_info = data.get("runtime_info") or {}
    if runtime_info:
        print_heading("Runtime Info")
        print(f"Return code: {runtime_info.get('returncode')}")
        stdout = runtime_info.get("stdout_tail") or ""
        if stdout:
            print(stdout.strip())


def build_scientific_receipt(client: CRAClient, title: str, tag: str, event_limit: int) -> Dict[str, Any]:
    """Collect a compact run receipt and write it to the Research Notepad."""
    sections: Dict[str, Any] = {}
    for name, method, path in [
        ("status", "GET", "/api/cra/status"),
        ("system", "GET", "/api/cra/system/state"),
        ("swarm", "GET", "/api/cra/diagnostics/agent_swarm"),
        ("exporter", "GET", "/api/cra/diagnostics/checkpoint_status"),
        ("notepad", "GET", "/api/research-notepad/summary"),
    ]:
        try:
            sections[name] = client.request_json(method, path)
        except Exception as exc:
            sections[name] = {"error": str(exc)}
    try:
        sections["events"] = client.request_json("GET", "/api/cra/events/recent")
    except Exception as exc:
        sections["events"] = {"error": str(exc)}

    status = sections.get("status", {})
    system = sections.get("system", {})
    swarm = sections.get("swarm", {})
    notepad = sections.get("notepad", {})
    content_lines = [
        f"{title} {tag}".strip(),
        "",
        f"Status keys: {', '.join(status.keys()) if isinstance(status, dict) else 'unavailable'}",
        f"System keys: {', '.join(system.keys()) if isinstance(system, dict) else 'unavailable'}",
        f"Swarm available: {'error' not in swarm if isinstance(swarm, dict) else False}",
        f"Notepad total: {((notepad.get('summary') or {}).get('total') if isinstance(notepad, dict) else 'unavailable')}",
        f"Recent event limit requested: {event_limit}",
        "",
        "Receipt JSON:",
        json.dumps(sections, indent=2, default=str)[:12000],
    ]
    note = client.request_json(
        "POST",
        "/api/research-notepad",
        payload={
            "type": "analysis",
            "content": "\n".join(content_lines),
            "metadata": {"source": "cra_cli", "kind": "scientific_receipt"},
        },
    )
    return {"receipt": sections, "notepad": note}


def parse_query_pairs(items: List[str]) -> Dict[str, str]:
    query: Dict[str, str] = {}
    for item in items:
        if "=" not in item:
            raise SystemExit(f"Invalid --query value {item!r}; expected key=value")
        key, value = item.split("=", 1)
        query[key] = value
    return query


def run_repl(client: CRAClient, args: argparse.Namespace) -> int:
    print("CRA SSH shell. Type /help for commands, /exit to quit.")
    while True:
        try:
            line = input("cra> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0

        if not line:
            continue
        if line in {"/exit", "/quit"}:
            return 0
        if line == "/help":
            print(
                "Local commands:\n"
                "  /status\n"
                "  /health\n"
                "  /system\n"
                "  /models [query]\n"
                "  /events\n"
                "  /logs [name]\n"
                "  /sim status|start|stop\n"
                "  /butterfly <message>\n"
                "  /organism <organism_id> <message>\n"
                "  /swarm\n"
                "  /exit\n"
                "Anything else is sent to the CRA chat model."
            )
            continue

        try:
            if line == "/status":
                summarize_status(client.request_json("GET", "/api/cra/status"))
            elif line == "/health":
                summarize_health(client.request_json("GET", "/api/cra/health/check"))
            elif line == "/system":
                summarize_system(client.request_json("GET", "/api/cra/system/state"))
            elif line.startswith("/models"):
                parts = line.split(maxsplit=1)
                query = parts[1].strip() if len(parts) > 1 else ""
                summarize_models(client.request_json(
                    "GET",
                    "/api/cra/hub/search",
                    query={"q": query, "limit": 10, "pipeline": "text-generation"},
                ))
            elif line == "/events":
                summarize_events(client.request_json("GET", "/api/cra/events/recent"), limit=10)
            elif line.startswith("/logs"):
                parts = line.split(maxsplit=1)
                log_name = parts[1].strip() if len(parts) > 1 else None
                summarize_logs(client.request_json("GET", "/api/cra/logs"), log_name=log_name, tail=20)
            elif line.startswith("/sim"):
                parts = line.split()
                action = parts[1] if len(parts) > 1 else "status"
                if action == "status":
                    summarize_sim_status(client.request_json("GET", "/api/simulation/status"))
                elif action == "start":
                    summarize_sim_status(client.request_json("POST", "/api/simulation/start", payload={}))
                elif action == "stop":
                    summarize_sim_status(client.request_json("POST", "/api/simulation/stop", payload={}))
                else:
                    print("Unknown /sim action. Use status, start, or stop.")
            elif line.startswith("/butterfly "):
                message = line.split(maxsplit=1)[1].strip()
                data = client.request_json("POST", "/api/butterfly/chat", payload={
                    "message": message,
                    "routing_strategy": "all",
                    "max_organisms": 10,
                    "min_mastery_level": 0,
                })
                summarize_butterfly_chat(data)
            elif line.startswith("/organism "):
                parts = line.split(maxsplit=2)
                if len(parts) < 3:
                    print("Usage: /organism <organism_id> <message>")
                    continue
                data = client.request_json(
                    "POST",
                    f"/api/organism/{parse.quote(parts[1])}/chat",
                    payload={"message": parts[2]},
                )
                summarize_organism_chat(data)
            elif line == "/swarm":
                summarize_swarm_stats(client.request_json("GET", "/api/cra/diagnostics/agent_swarm"))
            else:
                reply = do_chat(
                    client,
                    message=line,
                    model=args.model,
                    vision_model=args.vision_model,
                    api_key=args.api_key,
                    inference_provider=args.inference_provider,
                )
                summarize_chat(reply)
        except Exception as exc:
            print(f"Error: {exc}", file=sys.stderr)


def main() -> int:
    args = parse_args()
    client = CRAClient(base_url=args.base_url, timeout=args.timeout)

    try:
        if args.command == "status":
            data = client.request_json("GET", "/api/cra/status")
            if args.json:
                print_json(data)
            else:
                summarize_status(data)
            return 0

        if args.command == "sitrep":
            status_data = client.request_json("GET", "/api/cra/status")
            health_data = client.request_json("GET", "/api/cra/health/check")
            system_data = client.request_json("GET", "/api/cra/system/state")
            checkpoint_data = client.request_json("GET", "/api/cra/diagnostics/checkpoint_status")
            if args.json:
                print_json(
                    {
                        "status": status_data,
                        "health": health_data,
                        "system": system_data,
                        "checkpoint": checkpoint_data,
                    }
                )
            else:
                summarize_sitrep(status_data, health_data, system_data, checkpoint_data)
            return 0

        if args.command == "health":
            data = client.request_json("GET", "/api/cra/health/check")
            if args.json:
                print_json(data)
            else:
                summarize_health(data)
            return 0

        if args.command == "system":
            data = client.request_json("GET", "/api/cra/system/state")
            if args.json:
                print_json(data)
            else:
                summarize_system(data)
            return 0

        if args.command == "data":
            data = client.request_json("GET", "/api/cra/data")
            print_json(data if args.json else data.get("data", data))
            return 0

        if args.command == "models":
            data = client.request_json(
                "GET",
                "/api/cra/hub/search",
                query={
                    "q": args.query,
                    "limit": args.limit,
                    "pipeline": args.pipeline,
                },
            )
            if args.json:
                print_json(data)
            else:
                summarize_models(data)
            return 0

        if args.command == "sim-status":
            data = client.request_json("GET", "/api/simulation/status")
            if args.json:
                print_json(data)
            else:
                summarize_sim_status(data)
            return 0

        if args.command == "sim-start":
            data = client.request_json("POST", "/api/simulation/start", payload={})
            if args.json:
                print_json(data)
            else:
                summarize_sim_status(data)
            return 0

        if args.command == "sim-stop":
            data = client.request_json("POST", "/api/simulation/stop", payload={})
            if args.json:
                print_json(data)
            else:
                summarize_sim_status(data)
            return 0

        if args.command == "guardian-on":
            data = client.request_json(
                "POST",
                "/api/cra/guardian/mode",
                payload={"mode": "enable"},
            )
            print_json(data)
            return 0

        if args.command == "events":
            data = client.request_json("GET", "/api/cra/events/recent")
            if args.json:
                print_json(data)
            else:
                summarize_events(data, limit=args.limit)
            return 0

        if args.command == "logs":
            data = client.request_json("GET", "/api/cra/logs")
            if args.json:
                print_json(data)
            else:
                summarize_logs(data, log_name=args.log, tail=args.tail)
            return 0

        if args.command == "training-status":
            system_data = client.request_json("GET", "/api/cra/system/state")
            checkpoint_data = client.request_json("GET", "/api/cra/diagnostics/checkpoint_status")
            logs_data = client.request_json("GET", "/api/cra/logs")
            if args.json:
                print_json(
                    {
                        "system": system_data,
                        "checkpoint": checkpoint_data,
                        "logs": logs_data,
                    }
                )
            else:
                summarize_training_status(system_data, checkpoint_data, logs_data)
            return 0

        if args.command == "exporter-status":
            organisms_data = client.request_json("GET", "/api/organisms")
            capsules_data = client.request_json("GET", "/api/capsules")
            checkpoint_data = client.request_json("GET", "/api/cra/diagnostics/checkpoint_status")
            if args.json:
                print_json(
                    {
                        "organisms": organisms_data,
                        "capsules": capsules_data,
                        "checkpoint": checkpoint_data,
                    }
                )
            else:
                summarize_exporter_status(organisms_data, capsules_data, checkpoint_data)
            return 0

        if args.command == "security-contracts":
            data = client.request_json("GET", "/api/security/contracts")
            print_json(data)
            return 0

        if args.command == "security-receipts":
            data = client.request_json(
                "GET",
                "/api/security/receipts",
                query={"limit": args.limit, "action": args.action},
            )
            print_json(data)
            return 0

        if args.command == "config":
            if args.history:
                data = client.request_json(
                    "GET",
                    "/api/config/history",
                    query={"include_config": "false"},
                )
            elif args.actions:
                data = client.request_json(
                    "GET",
                    "/api/config/actions",
                    query={"limit": args.limit},
                )
            elif args.current:
                data = client.request_json("GET", "/api/config/current")
            else:
                data = client.request_json("GET", "/api/cra/config")
            if args.json:
                print_json(data)
            else:
                summarize_config(data, limit=args.limit)
            return 0

        if args.command == "config-set":
            patch: List[Dict[str, Any]] = [{"op": args.op, "path": args.path}]
            if args.op != "remove":
                patch[0]["value"] = parse_jsonish_value(args.value)
            data = client.request_json(
                "POST",
                "/api/config/update",
                payload={
                    "patch": patch,
                    "actor": "CRA_CLI",
                    "reason": args.reason,
                },
            )
            print_json(data if args.json else data)
            return 0

        if args.command == "config-rollback":
            data = client.request_json(
                "POST",
                "/api/config/rollback",
                payload={
                    "steps": args.steps,
                    "actor": "CRA_CLI",
                    "reason": args.reason,
                },
            )
            print_json(data if args.json else data)
            return 0

        if args.command == "organisms":
            data = client.request_json("GET", "/api/organisms")
            if args.json:
                print_json(data)
            else:
                summarize_organisms(data, limit=args.limit)
            return 0

        if args.command == "alliances":
            data = client.request_json("GET", "/api/alliances")
            if args.json:
                print_json(data)
            else:
                summarize_alliances(data, limit=args.limit)
            return 0

        if args.command == "capsules":
            data = client.request_json("GET", "/api/capsules")
            if args.json:
                print_json(data)
            else:
                summarize_capsules(data)
            return 0

        if args.command == "checkpoint-status":
            data = client.request_json("GET", "/api/cra/diagnostics/checkpoint_status")
            if args.json:
                print_json(data)
            else:
                summarize_checkpoints(data)
            return 0

        if args.command == "checkpoint-list":
            data = client.request_json("GET", "/api/checkpoint/list")
            if args.json:
                print_json(data)
            else:
                summarize_checkpoints(data)
            return 0

        if args.command == "checkpoint-save":
            data = client.request_json(
                "POST",
                "/api/checkpoint/save",
                payload={"reason": args.reason, "actor": "CRA_CLI"},
            )
            print_json(data if args.json else data)
            return 0

        if args.command == "checkpoint-restore":
            payload: Dict[str, Any] = {
                "actor": "CRA_CLI",
                "reason": args.reason,
            }
            if args.name:
                payload["checkpoint_name"] = args.name
            data = client.request_json("POST", "/api/checkpoint/restore", payload=payload)
            print_json(data if args.json else data)
            return 0

        if args.command == "chat":
            message = read_message(args)
            data = do_chat(
                client,
                message=message,
                model=args.model,
                vision_model=args.vision_model,
                api_key=args.api_key,
                selected_event=args.selected_event,
                view_state=read_view_state(args.view_state_file),
                inference_provider=args.inference_provider,
            )
            if args.json:
                print_json(data)
            else:
                summarize_chat(data)
            return 0

        if args.command in ("butterfly-chat", "standin-chat"):
            message = read_message(args)
            actor = "CRA_STANDIN" if args.command == "standin-chat" else "CRA_CLI"
            data = client.request_json("POST", "/api/butterfly/chat", payload={
                "message": message,
                "routing_strategy": args.routing_strategy,
                "max_organisms": args.max_organisms,
                "min_mastery_level": args.min_mastery_level,
                "actor": actor,
                "interaction_context": {
                    "source": args.command,
                    "inside_boundary": "inside_game_only",
                    "consent_condition": "operator_requested",
                },
            })
            if args.json:
                print_json(data)
            else:
                summarize_butterfly_chat(data)
            return 1 if butterfly_chat_failed(data) else 0

        if args.command == "organism-chat":
            message = read_message(args)
            data = client.request_json(
                "POST",
                f"/api/organism/{parse.quote(args.organism_id)}/chat",
                payload={"message": message, "actor": "CRA_CLI"},
            )
            if args.json:
                print_json(data)
            else:
                summarize_organism_chat(data)
            return 0

        if args.command == "swarm-stats":
            data = client.request_json("GET", "/api/cra/diagnostics/agent_swarm")
            if args.json:
                print_json(data)
            else:
                summarize_swarm_stats(data)
            return 0

        if args.command == "notepad":
            if args.summary:
                data = client.request_json("GET", "/api/research-notepad/summary")
                if args.json:
                    print_json(data)
                else:
                    summarize_notepad(data, summary_only=True)
                return 0

            data = client.request_json(
                "GET",
                "/api/research-notepad",
                query={
                    "type": args.type,
                    "query": args.query,
                    "limit": args.limit,
                },
            )
            if args.json:
                print_json(data)
            else:
                summarize_notepad(data)
            return 0

        if args.command == "notepad-add":
            content = read_message(args)
            metadata: Dict[str, Any] = {"source": args.source}
            if args.confidence:
                metadata["confidence"] = args.confidence
            if args.cause:
                metadata["causeEventId"] = args.cause
            if args.effect:
                metadata["effectEventId"] = args.effect
            payload = {
                "type": args.type,
                "content": content,
                "metadata": metadata,
                "linkedEvents": args.event,
                "actor": "CRA_CLI",
            }
            data = client.request_json("POST", "/api/research-notepad", payload=payload)
            if args.json:
                print_json(data)
            else:
                entry = data.get("entry", {})
                print(f"Added {entry.get('type', args.type)} note: {entry.get('id', '-')}")
            return 0

        if args.command == "cocoon-validate":
            data = validate_cocoon_package(
                Path(args.path),
                run_info=args.run_info,
                python_executable=args.python,
            )
            if args.json:
                print_json(data)
            else:
                summarize_cocoon_validation(data)
            return 0

        if args.command == "scientific-receipt":
            data = build_scientific_receipt(
                client,
                title=args.title,
                tag=args.tag,
                event_limit=args.event_limit,
            )
            if args.json:
                print_json(data)
            else:
                entry = (data.get("notepad") or {}).get("entry", {})
                print(f"Scientific receipt saved to Research Notepad: {entry.get('id', '-')}")
            return 0

        if args.command == "repl":
            return run_repl(client, args)

        if args.command == "compile-organism":
            data = client.request_json(
                "POST",
                f"/api/capsule/{args.organism_id}/compile",
                payload={"format": args.format},
            )
            saved_paths = save_downloads(client, data, args.outdir)
            if args.json:
                print_json(data)
            else:
                summarize_export_result(data, saved_paths)
            return 0

        if args.command == "compile-ensemble":
            data = client.request_json(
                "POST",
                "/api/capsules/compile-ensemble",
                payload={"organism_ids": args.organism_ids, "format": args.format},
            )
            saved_paths = save_downloads(client, data, args.outdir)
            if args.json:
                print_json(data)
            else:
                summarize_export_result(data, saved_paths)
            return 0

        if args.command == "compile-learning":
            payload = {
                "organism_ids": args.organism_ids,
                "training_config": read_json_file(args.training_config_file),
            }
            data = client.request_json("POST", "/api/capsules/compile-learning", payload=payload)
            saved_paths = save_downloads(client, data, args.outdir)
            if args.json:
                print_json(data)
            else:
                summarize_export_result(data, saved_paths)
            return 0

        if args.command == "compile-cocoon":
            selected_alliances = list(args.alliance_ids or []) + list(args.alliance_names or [])
            payload = {
                "organism_ids": args.organism_ids,
                "top_n": args.top_n,
                "include_gym": not args.no_gym,
                "include_http": not args.no_http,
                "compress": not args.no_compress,
                "format": args.format,
                "actor": "CRA_CLI",
                "reason": args.reason,
            }
            if selected_alliances:
                payload["selected_alliances"] = selected_alliances
            if args.include_unallied:
                payload["include_unallied"] = True
            data = client.request_json("POST", "/api/capsules/compile-cocoon", payload=payload)
            saved_paths = save_downloads(client, data, args.outdir)
            if args.json:
                print_json(data)
            else:
                summarize_export_result(data, saved_paths)
            return 0

        if args.command == "api":
            payload = json.loads(args.data) if args.data else None
            query = parse_query_pairs(args.query)
            data = client.request_json(args.method, args.path, payload=payload, query=query)
            print_json(data)
            return 0

        raise SystemExit(f"Unknown command: {args.command}")
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
