#!/usr/bin/env python3
"""Rebuild marked sections of memory/INDEX.md from ledger and session JSONL."""
from __future__ import annotations
import argparse
from datetime import datetime
import json
from pathlib import Path
import sys

ACTIVE_START = "<!-- PROJECT-MEMORY-LEDGER:ACTIVE:START -->"
ACTIVE_END = "<!-- PROJECT-MEMORY-LEDGER:ACTIVE:END -->"
SESSIONS_START = "<!-- PROJECT-MEMORY-LEDGER:SESSIONS:START -->"
SESSIONS_END = "<!-- PROJECT-MEMORY-LEDGER:SESSIONS:END -->"
ACTIVE_STATES = {"candidate", "verified", "in_memory", "in_agents"}


def read_jsonl(path: Path):
    result = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{number}: invalid JSON: {exc.msg}") from exc
        if not isinstance(obj, dict):
            raise ValueError(f"{path}:{number}: JSONL row must be an object")
        result.append(obj)
    return result


def md(value) -> str:
    if value is None or value == "":
        return "—"
    return str(value).replace("|", "\\|").replace("\r", " ").replace("\n", " ").strip()


def replace_block(text: str, start: str, end: str, content: str) -> str:
    if text.count(start) != 1 or text.count(end) != 1:
        raise ValueError(f"Expected exactly one pair of markers: {start} ... {end}")
    a = text.index(start) + len(start)
    b = text.index(end)
    if b < a:
        raise ValueError(f"Marker order is invalid: {start} must precede {end}")
    return text[:a] + "\n" + content.rstrip() + "\n" + text[b:]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=".", help="Target project root")
    args = ap.parse_args()
    root = Path(args.root).expanduser().resolve()
    ledger_path = root / "memory" / "ledger.jsonl"
    index_path = root / "memory" / "INDEX.md"
    sessions_path = root / "memory" / "sessions"
    if not ledger_path.is_file() or not index_path.is_file():
        print("ERROR: memory/ledger.jsonl and memory/INDEX.md must exist. Initialize first.", file=sys.stderr)
        return 2
    try:
        ledger_events = read_jsonl(ledger_path)
        latest = {}
        for event in ledger_events:
            mid = event.get("memory_id")
            record = event.get("record")
            if not isinstance(mid, str) or not isinstance(record, dict):
                raise ValueError(f"Ledger event is missing memory_id or record snapshot: {event.get('event_id', '<unknown>')}")
            latest[mid] = record
        active = []
        for mid, rec in sorted(latest.items(), key=lambda pair: (pair[1].get("status", ""), pair[0])):
            if rec.get("status") in ACTIVE_STATES:
                refs = rec.get("evidence_refs") or []
                ref_text = "; ".join(str(ref) for ref in refs[:2])
                if len(refs) > 2:
                    ref_text += f"; +{len(refs)-2} more"
                destination = rec.get("destination", "—")
                linktext = md(ref_text or "no evidence")
                active.append(f"| `{md(mid)}` | {md(rec.get('status'))} | {md(rec.get('kind'))} | {md(rec.get('scope'))} | {md(rec.get('title') or rec.get('claim'))} | {linktext}; `{md(destination)}` |")
        if not active:
            active.append("| — | — | — | — | No active memory records | — |")

        sessions = []
        if sessions_path.exists():
            for path in sorted(sessions_path.rglob("*.jsonl"), reverse=True):
                rows = read_jsonl(path)
                if not rows:
                    continue
                start = next((r for r in rows if r.get("record_type") == "session_start"), {})
                end = next((r for r in reversed(rows) if r.get("record_type") == "session_end"), {})
                sid = start.get("session_id") or (rows[0].get("session_id") if rows else "unknown")
                date = end.get("ended_at") or start.get("started_at") or "unknown"
                try:
                    date_display = datetime.fromisoformat(str(date).replace("Z", "+00:00")).date().isoformat()
                except ValueError:
                    date_display = str(date)
                status = end.get("capture_status", "in_progress" if not end else "unknown")
                notes = end.get("notes") or start.get("notes") or ""
                rel = path.relative_to(root).as_posix()
                sessions.append((date_display, f"| `{md(sid)}` | {md(date_display)} | {md(status)} | [{md(notes or rel)}]({rel}) |"))
        sessions.sort(reverse=True)
        session_lines = [item[1] for item in sessions[:30]]
        if not session_lines:
            session_lines = ["| — | — | — | No session logs yet |"]

        text = index_path.read_text(encoding="utf-8")
        text = replace_block(text, ACTIVE_START, ACTIVE_END, "\n".join([
            "| ID | Status | Kind | Scope | Summary | Evidence / Destination |",
            "|---|---|---|---|---|---|",
            *active,
        ]))
        text = replace_block(text, SESSIONS_START, SESSIONS_END, "\n".join([
            "| Session ID | Date | Capture status | Notes |",
            "|---|---|---|---|",
            *session_lines,
        ]))
        index_path.write_text(text.rstrip() + "\n", encoding="utf-8")
        print(f"Updated marked index sections: {index_path}")
        print(f"Active memory IDs: {len(active) if active != ['| — | — | — | — | No active memory records | — |'] else 0}")
        print(f"Sessions listed: {len(session_lines) if session_lines != ['| — | — | — | No session logs yet |'] else 0}")
        return 0
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
