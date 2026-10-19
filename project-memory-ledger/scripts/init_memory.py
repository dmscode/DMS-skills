#!/usr/bin/env python3
"""Non-destructive bootstrapper for a Project Memory Ledger repository."""
from __future__ import annotations
import argparse
from pathlib import Path
import sys


def load_template(skill_root: Path, name: str) -> str:
    path = skill_root / "assets" / "templates" / name
    if not path.is_file():
        raise FileNotFoundError(f"Template not found: {path}")
    return path.read_text(encoding="utf-8")


def write_if_missing(path: Path, content: str) -> bool:
    if path.exists():
        print(f"KEEP existing: {path}")
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = content.rstrip()
    path.write_text((payload + "\n") if payload else "", encoding="utf-8")
    print(f"CREATE: {path}")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Target project root (default: current directory)")
    parser.add_argument("--patch-agents", action="store_true", help="Append a marked memory policy block to AGENTS.md if absent")
    args = parser.parse_args()
    project = Path(args.root).expanduser().resolve()
    if not project.exists() or not project.is_dir():
        print(f"ERROR: target root is not a directory: {project}", file=sys.stderr)
        return 2
    skill_root = Path(__file__).resolve().parents[1]

    (project / "memory" / "sessions").mkdir(parents=True, exist_ok=True)
    (project / "memory" / "records").mkdir(parents=True, exist_ok=True)
    (project / "memory" / "decisions").mkdir(parents=True, exist_ok=True)
    (project / "memory" / "archive").mkdir(parents=True, exist_ok=True)
    print(f"READY: {project / 'memory'} (existing files will not be overwritten)")

    write_if_missing(project / "memory.md", load_template(skill_root, "memory.md"))
    write_if_missing(project / "memory" / "README.md", load_template(skill_root, "README.md"))
    write_if_missing(project / "memory" / "INDEX.md", load_template(skill_root, "INDEX.md"))
    write_if_missing(project / "memory" / "ledger.jsonl", "")

    if args.patch_agents:
        agents = project / "AGENTS.md"
        marker_start = "<!-- PROJECT-MEMORY-LEDGER:START -->"
        marker_end = "<!-- PROJECT-MEMORY-LEDGER:END -->"
        block = load_template(skill_root, "AGENTS-memory-block.md").strip()
        if agents.exists():
            current = agents.read_text(encoding="utf-8")
            if marker_start in current and marker_end in current:
                print(f"KEEP existing marked memory block: {agents}")
            elif marker_start in current or marker_end in current:
                print(f"WARNING: incomplete markers in {agents}; not modifying it", file=sys.stderr)
            else:
                addition = f"\n\n{marker_start}\n{block}\n{marker_end}\n"
                agents.write_text(current.rstrip() + addition, encoding="utf-8")
                print(f"APPEND memory protocol block: {agents}")
        else:
            content = f"# Project Instructions\n\n{marker_start}\n{block}\n{marker_end}\n"
            agents.write_text(content, encoding="utf-8")
            print(f"CREATE with memory protocol block: {agents}")
    else:
        print("NOTE: AGENTS.md was not modified. Review assets/templates/AGENTS-memory-block.md and add it only if appropriate.")

    print("\nNext steps:")
    print("1. Review memory/README.md and decide whether raw session logs may be tracked in Git.")
    print("2. Read the Skill's references/PROTOCOL.md and adapt names to existing project conventions.")
    print("3. Run validate_memory.py after the first session and after promotions.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
