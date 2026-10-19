#!/usr/bin/env python3
"""Validate Project Memory Ledger JSONL and materialized-view consistency (stdlib only)."""
from __future__ import annotations
import argparse
from datetime import datetime
import json
from pathlib import Path
import re
import sys
from typing import Any

STATUSES = {"candidate", "verified", "in_memory", "in_agents", "superseded", "rejected", "archived"}
KINDS = {"project_fact", "decision", "constraint", "pitfall", "lesson", "workflow", "open_question", "preference", "hypothesis", "work_state"}
EVENT_TYPES = {"create", "verify", "revise", "promote_memory", "promote_agents", "supersede", "reject", "archive", "reopen"}
RECORD_FIELDS = {"title", "kind", "status", "claim", "scope", "confidence", "importance", "stability", "evidence_refs", "created_at", "updated_at", "valid_until", "related_ids", "destination", "superseded_by"}

class Validator:
    def __init__(self, root: Path):
        self.root = root
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, msg: str) -> None: self.errors.append(msg)
    def warn(self, msg: str) -> None: self.warnings.append(msg)

    @staticmethod
    def parse_dt(value: Any) -> bool:
        if not isinstance(value, str) or not value:
            return False
        try:
            datetime.fromisoformat(value.replace("Z", "+00:00"))
            return True
        except ValueError:
            return False

    def read_jsonl(self, path: Path) -> list[dict[str, Any]]:
        records = []
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError) as exc:
            self.error(f"{path}: cannot read UTF-8 text: {exc}")
            return records
        for line_no, raw in enumerate(lines, 1):
            if not raw.strip():
                self.error(f"{path}:{line_no}: blank lines are not allowed in JSONL")
                continue
            try:
                item = json.loads(raw)
            except json.JSONDecodeError as exc:
                self.error(f"{path}:{line_no}: invalid JSON: {exc.msg}")
                continue
            if not isinstance(item, dict):
                self.error(f"{path}:{line_no}: each JSONL record must be an object")
                continue
            records.append(item)
        return records

    def validate_sessions(self) -> tuple[set[str], set[str]]:
        known_messages: set[str] = set()
        known_sessions: set[str] = set()
        base = self.root / "memory" / "sessions"
        if not base.exists():
            self.warn(f"Missing directory: {base}")
            return known_messages, known_sessions
        for path in sorted(base.rglob("*.jsonl")):
            rows = self.read_jsonl(path)
            if not rows:
                self.warn(f"{path}: empty session file")
                continue
            if rows[0].get("record_type") != "session_start":
                self.error(f"{path}: first record must be session_start")
            session_ids = {r.get("session_id") for r in rows if isinstance(r.get("session_id"), str)}
            if len(session_ids) != 1:
                self.error(f"{path}: records must have exactly one session_id")
                continue
            session_id = next(iter(session_ids))
            known_sessions.add(session_id)
            if not re.fullmatch(r"S-[A-Za-z0-9._-]+", session_id):
                self.warn(f"{path}: non-canonical session_id {session_id!r}")
            starts = [i for i, r in enumerate(rows) if r.get("record_type") == "session_start"]
            ends = [i for i, r in enumerate(rows) if r.get("record_type") == "session_end"]
            if len(starts) != 1:
                self.error(f"{path}: expected exactly one session_start, found {len(starts)}")
            if len(ends) > 1:
                self.error(f"{path}: at most one session_end is allowed")
            if ends and ends[0] != len(rows) - 1:
                self.error(f"{path}: session_end must be the last record")
            if not ends:
                self.warn(f"{path}: no session_end; session may still be open")
            seqs = []
            msg_ids = set()
            message_count = 0
            for i, row in enumerate(rows):
                if row.get("schema_version") != "1.0":
                    self.error(f"{path}: record {i+1}: schema_version must be '1.0'")
                rtype = row.get("record_type")
                if rtype not in {"session_start", "message", "session_end"}:
                    self.error(f"{path}: record {i+1}: unsupported record_type {rtype!r}")
                    continue
                dtfield = {"session_start": "started_at", "message": "timestamp", "session_end": "ended_at"}[rtype]
                if not self.parse_dt(row.get(dtfield)):
                    self.error(f"{path}: record {i+1}: {dtfield} must be an ISO-8601 timestamp with timezone")
                if rtype == "session_start":
                    if row.get("capture_status") != "in_progress":
                        self.error(f"{path}: session_start capture_status must be in_progress")
                    if not isinstance(row.get("source_agent"), str) or not row.get("source_agent"):
                        self.error(f"{path}: session_start needs source_agent")
                elif rtype == "message":
                    message_count += 1
                    if starts and i < starts[0]:
                        self.error(f"{path}: message cannot precede session_start")
                    if ends and i > ends[0]:
                        self.error(f"{path}: message cannot follow session_end")
                    mid = row.get("message_id")
                    seq = row.get("sequence")
                    if not isinstance(mid, str) or not re.fullmatch(r"MSG-[0-9]{6,}", mid):
                        self.error(f"{path}: record {i+1}: message_id must look like MSG-000001")
                    elif mid in msg_ids:
                        self.error(f"{path}: duplicate message_id {mid}")
                    else:
                        msg_ids.add(mid)
                        known_messages.add(f"{path.relative_to(self.root).as_posix()}#{mid}")
                    if not isinstance(seq, int) or isinstance(seq, bool) or seq < 1:
                        self.error(f"{path}: record {i+1}: sequence must be a positive integer")
                    else:
                        seqs.append(seq)
                    if row.get("role") not in {"system", "developer", "user", "assistant", "tool"}:
                        self.error(f"{path}: record {i+1}: invalid role")
                    if not isinstance(row.get("content"), str):
                        self.error(f"{path}: record {i+1}: content must be a string")
                elif rtype == "session_end":
                    if row.get("capture_status") not in {"complete", "partial", "summary_only"}:
                        self.error(f"{path}: session_end capture_status must be complete, partial, or summary_only")
                    if row.get("message_count") != message_count:
                        self.warn(f"{path}: session_end message_count does not match actual message count ({message_count})")
            if seqs and sorted(seqs) != list(range(1, len(seqs) + 1)):
                self.error(f"{path}: message sequence values must be unique and contiguous starting at 1")
            if ends and rows[ends[0]].get("message_count") != message_count:
                self.warn(f"{path}: session_end count mismatch")
        return known_messages, known_sessions

    def validate_ledger(self, known_messages: set[str]) -> dict[str, dict[str, Any]]:
        path = self.root / "memory" / "ledger.jsonl"
        if not path.exists():
            self.warn(f"Missing ledger: {path}")
            return {}
        rows = self.read_jsonl(path)
        event_ids: set[str] = set()
        histories: dict[str, list[dict[str, Any]]] = {}
        allowed_transitions = {
            "create": (None, "candidate"),
            "verify": ({"candidate"}, "verified"),
            "promote_memory": ({"verified"}, "in_memory"),
            "promote_agents": ({"verified", "in_memory"}, "in_agents"),
            "supersede": ({"candidate", "verified", "in_memory", "in_agents"}, "superseded"),
            "reject": ({"candidate", "verified"}, "rejected"),
            "archive": ({"superseded", "rejected"}, "archived"),
            "reopen": ({"superseded", "rejected", "archived"}, "candidate"),
            "revise": ("same", None),
        }
        for line_no, row in enumerate(rows, 1):
            label = f"{path}:{line_no}"
            if row.get("schema_version") != "1.0": self.error(f"{label}: schema_version must be '1.0'")
            for fld in ("event_id", "memory_id", "event_type", "actor", "reason"):
                if not isinstance(row.get(fld), str) or not row.get(fld): self.error(f"{label}: missing/non-string {fld}")
            if not self.parse_dt(row.get("timestamp")): self.error(f"{label}: timestamp must be ISO-8601 with timezone")
            eid, mid, etype = row.get("event_id"), row.get("memory_id"), row.get("event_type")
            if isinstance(eid, str):
                if eid in event_ids: self.error(f"{label}: duplicate event_id {eid}")
                event_ids.add(eid)
            if etype not in EVENT_TYPES:
                self.error(f"{label}: unsupported event_type {etype!r}")
                continue
            rec = row.get("record")
            if not isinstance(rec, dict):
                self.error(f"{label}: record must be an object")
                continue
            missing = RECORD_FIELDS - set(rec)
            if missing: self.error(f"{label}: record missing fields: {', '.join(sorted(missing))}")
            if rec.get("kind") not in KINDS: self.error(f"{label}: invalid record.kind {rec.get('kind')!r}")
            if rec.get("status") not in STATUSES: self.error(f"{label}: invalid record.status {rec.get('status')!r}")
            for fld in ("created_at", "updated_at"):
                if not self.parse_dt(rec.get(fld)): self.error(f"{label}: record.{fld} must be ISO-8601 with timezone")
            if rec.get("valid_until") is not None and not self.parse_dt(rec.get("valid_until")):
                self.error(f"{label}: record.valid_until must be null or ISO-8601 with timezone")
            if rec.get("confidence") not in {"low", "medium", "high"}: self.error(f"{label}: invalid confidence")
            if rec.get("importance") not in {"low", "medium", "high"}: self.error(f"{label}: invalid importance")
            if rec.get("stability") not in {"volatile", "recurring", "durable"}: self.error(f"{label}: invalid stability")
            if not isinstance(rec.get("evidence_refs"), list): self.error(f"{label}: evidence_refs must be a list")
            elif any(not isinstance(ref, str) or not ref.strip() for ref in rec.get("evidence_refs", [])):
                self.error(f"{label}: evidence_refs must contain non-empty strings only")
            if etype in {"create", "verify", "promote_memory", "promote_agents", "reopen"} and not rec.get("evidence_refs"):
                self.error(f"{label}: {etype} requires at least one evidence_ref")
            for fld in ("title", "claim", "scope", "destination"):
                if not isinstance(rec.get(fld), str) or not rec.get(fld).strip():
                    self.error(f"{label}: record.{fld} must be a non-empty string")
            if not isinstance(rec.get("related_ids"), list): self.error(f"{label}: related_ids must be a list")
            if rec.get("superseded_by") is not None and not isinstance(rec.get("superseded_by"), str):
                self.error(f"{label}: superseded_by must be a memory ID string or null")
            if etype == "promote_memory" and rec.get("destination") != "memory.md":
                self.error(f"{label}: promote_memory destination must be memory.md")
            if etype == "promote_agents" and rec.get("destination") != "AGENTS.md":
                self.error(f"{label}: promote_agents destination must be AGENTS.md")
            if etype == "reopen" and rec.get("superseded_by") is not None:
                self.error(f"{label}: reopened candidate must clear superseded_by")
            if etype == "create" and rec.get("status") != "candidate": self.error(f"{label}: create must have status candidate")
            expected = allowed_transitions.get(etype)
            hist = histories.setdefault(str(mid), [])
            previous_status = hist[-1].get("record", {}).get("status") if hist else None
            if expected:
                from_states, target = expected
                if etype == "create":
                    if hist: self.error(f"{label}: create used for existing memory_id {mid}")
                elif etype == "revise":
                    if not hist: self.error(f"{label}: revise used before create for {mid}")
                    elif previous_status in {"superseded", "rejected", "archived"}:
                        self.error(f"{label}: cannot revise terminal state {previous_status}; use reopen if justified")
                    elif rec.get("status") != previous_status:
                        self.error(f"{label}: revise must preserve status (was {previous_status})")
                else:
                    if not hist: self.error(f"{label}: {etype} used before create for {mid}")
                    elif previous_status not in from_states:
                        self.error(f"{label}: {etype} transition not allowed from {previous_status} for {mid}")
                    if rec.get("status") != target:
                        self.error(f"{label}: {etype} requires status {target}")
            if etype == "supersede" and not rec.get("superseded_by"):
                self.error(f"{label}: supersede must set superseded_by")
            if etype == "create" and not isinstance(rec.get("evidence_refs"), list):
                self.error(f"{label}: evidence_refs must be a list")
            for ref in rec.get("evidence_refs", []) if isinstance(rec.get("evidence_refs"), list) else []:
                if not isinstance(ref, str):
                    self.error(f"{label}: evidence refs must be strings")
                    continue
                if "#MSG-" in ref and ref.startswith("memory/sessions/"):
                    file_part, msg_id = ref.split("#", 1)
                    target_path = self.root / file_part
                    normalized = f"{file_part}#{msg_id}"
                    if not target_path.exists():
                        self.warn(f"{label}: local evidence file missing: {file_part}")
                    elif normalized not in known_messages:
                        self.warn(f"{label}: local message reference not found: {ref}")
            hist.append(row)

        latest = {mid: rows[-1].get("record", {}) for mid, rows in histories.items() if rows}
        for old_mid, rec in latest.items():
            replacement = rec.get("superseded_by")
            if rec.get("status") == "superseded" and replacement and replacement not in histories:
                self.warn(f"{old_mid}: superseded_by points to unknown memory ID {replacement}")
        agents_path = self.root / "AGENTS.md"
        mem_path = self.root / "memory.md"
        index_path = self.root / "memory" / "INDEX.md"
        agents_text = agents_path.read_text(encoding="utf-8", errors="replace") if agents_path.exists() else ""
        mem_text = mem_path.read_text(encoding="utf-8", errors="replace") if mem_path.exists() else ""
        idx_text = index_path.read_text(encoding="utf-8", errors="replace") if index_path.exists() else ""
        for mid, rec in latest.items():
            status = rec.get("status")
            if status == "in_agents" and mid not in agents_text:
                self.warn(f"{mid}: latest ledger status is in_agents but ID is missing from AGENTS.md")
            if status == "in_memory" and mid not in mem_text:
                self.warn(f"{mid}: latest ledger status is in_memory but ID is missing from memory.md")
            if status in {"candidate", "verified", "in_memory", "in_agents"} and mid not in idx_text:
                self.warn(f"{mid}: active record missing from memory/INDEX.md")
            if status in {"superseded", "rejected", "archived"} and (mid in agents_text or mid in mem_text):
                self.warn(f"{mid}: terminal record ID still appears in AGENTS.md or memory.md; ensure it is clearly marked historical or removed from current views")
        return latest

    def run(self) -> int:
        memory_dir = self.root / "memory"
        if not memory_dir.exists():
            self.warn(f"Memory directory does not exist: {memory_dir}")
            print("No memory directory found; run init_memory.py if you intend to initialize this project.")
        known_messages, _ = self.validate_sessions()
        latest = self.validate_ledger(known_messages)
        print(f"Checked project: {self.root}")
        print(f"Current memory IDs found in ledger: {len(latest)}")
        for warning in self.warnings:
            print(f"WARNING: {warning}")
        for error in self.errors:
            print(f"ERROR: {error}")
        if self.errors:
            print(f"\nValidation failed: {len(self.errors)} error(s), {len(self.warnings)} warning(s).")
            return 1
        print(f"\nValidation passed with {len(self.warnings)} warning(s). Note: syntax consistency does not prove claim truth or completeness.")
        return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=".", help="Target project root (default: current directory)")
    args = ap.parse_args()
    root = Path(args.root).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        print(f"ERROR: target root is not a directory: {root}", file=sys.stderr)
        return 2
    return Validator(root).run()

if __name__ == "__main__":
    raise SystemExit(main())
