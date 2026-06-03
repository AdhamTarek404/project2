"""
Helpers for Cowrie JSON enrichment: timestamps, TTY paths, LLM-safe session intel.
""
from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional


def cowrie_home() -> str:
    return os.path.expanduser("~/cowrie")


def parse_cowrie_timestamp(ts: Optional[str]) -> Optional[datetime]:
    if not ts or not isinstance(ts, str):
        return None
    try:
        if ts.endswith("Z"):
            ts = ts[:-1] + "+00:00"
        return datetime.fromisoformat(ts)
    except (ValueError, TypeError):
        return None


def resolve_tty_path(ttylog_filename: Optional[str]) -> Optional[str]:
    """Return absolute path to TTY recording if file exists (Cowrie state_path/tty)."""
    if not ttylog_filename:
        return None
    base = os.path.join(cowrie_home(), "var", "lib", "cowrie", "tty")
    path = os.path.join(base, ttylog_filename)
    if os.path.isfile(path):
        return path
    # Some installs use state_path only under cowrie install dir
    alt = os.path.join(cowrie_home(), "tty", ttylog_filename)
    if os.path.isfile(alt):
        return alt
    return ttylog_filename if ttylog_filename else None


def new_session_state(src_ip: str) -> Dict[str, Any]:
    return {
        "src_ip": src_ip,
        "commands": [],
        "threat_score": 0.0,
        "attack_type": "Unknown",
        "predicted_next": "Unknown",
        "reasoning": "",
        "confidence": "low",
        "blocked": False,
        "llm_call_count": 0,
        "login_fail_count": 0,
        "login_success_count": 0,
        "download_count": 0,
        "upload_count": 0,
        "pubkey_count": 0,
        "kex_json": None,
        "connected_at": None,
        "closed_at": None,
        "duration_from_cowrie": None,
        "client_version": None,
        "hassh": None,
        "kex_algorithms": None,
        "session_arch": None,
        "login_rows": [],
        "downloads": [],
        "uploads": [],
        "pubkey_attempts": [],
        "ttylog_filename": None,
        "ttylog_size": None,
        "ttylog_shasum": None,
    }


def redact_password(pw: Optional[str]) -> str:
    if not pw:
        return ""
    if len(pw) <= 2:
        return "[REDACTED]"
    return f"{pw[0]}…[REDACTED] (len {len(pw)})"


def format_session_intel_for_llm(session: Dict[str, Any]) -> str:
    """Plain-text block for forensic / classification prompts (passwords redacted)."""
    lines: List[str] = []
    ca = session.get("connected_at")
    if ca:
        lines.append(
            f"- Session started (logged): {ca.isoformat() if isinstance(ca, datetime) else ca}"
        )
    if session.get("client_version"):
        lines.append(f"- SSH client version: {session['client_version']}")
    if session.get("hassh"):
        lines.append(f"- HASSH fingerprint: {session['hassh']}")
    if session.get("session_arch"):
        lines.append(f"- Reported arch (session.params): {session['session_arch']}")

    dwell = session.get("dwell_seconds")
    if dwell is not None:
        lines.append(f"- Dwell time (seconds): {dwell:.2f}" if isinstance(dwell, float) else f"- Dwell time (seconds): {dwell}")

    if session.get("ttylog_filename"):
        lines.append(f"- TTY recording file: {session['ttylog_filename']}")
        tp = session.get("tty_resolved_path")
        if tp:
            lines.append(f"- TTY path on sensor: {tp}")

    rows = session.get("login_rows") or []
    if rows:
        lines.append("- Authentication activity:")
        for r in rows[-20:]:
            ev = r.get("event_type", "")
            user = r.get("username", "")
            if ev == "cowrie.client.fingerprint":
                lines.append(
                    f"  · Public key attempt user={user} fp={r.get('fingerprint', '')[:40]}… type={r.get('key_type', '')}"
                )
            else:
                ok = r.get("success")
                pwd = redact_password(r.get("password"))
                lines.append(
                    f"  · {ev} user={user} success={ok} password={pwd or 'n/a'}"
                )

    downs = session.get("downloads") or []
    if downs:
        lines.append("- Files downloaded (URLs / hashes):")
        for d in downs[-15:]:
            lines.append(f"  · url={d.get('url', '')} sha256={d.get('shasum', '')} outfile={d.get('outfile', '')}")

    ups = session.get("uploads") or []
    if ups:
        lines.append("- Files uploaded:")
        for u in ups[-15:]:
            lines.append(
                f"  · name={u.get('filename', '')} sha256={u.get('shasum', '')} outfile={u.get('outfile', '')}"
            )

    if not lines:
        return ""
    return "ADDITIONAL COWRIE SESSION INTELLIGENCE:\n" + "\n".join(lines)


def kex_payload_for_db(data: Dict[str, Any]) -> str:
    """Serialize kex-relevant fields for storage."""
    subset = {
        "hassh": data.get("hassh"),
        "hasshAlgorithms": data.get("hasshAlgorithms"),
        "kexAlgs": data.get("kexAlgs"),
        "keyAlgs": data.get("keyAlgs"),
    }
    try:
        return json.dumps(subset, default=str)[:8000]
    except Exception:
        return ""
