"""Host mirrors of the single-source skills (section 159).

``skills/<name>/SKILL.md`` is the only editable copy. Mirrors are rendered deterministically
for each agent host under a ``sparkforge-azure-`` prefix so they never collide with
spark-forge-aws skills of the same name.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from sparkforge_azure.skills.model import discover_skill_files, split_front_matter

MIRROR_PREFIX = "sparkforge-azure-"
#: Host mirror roots, relative to the repository root.
MIRROR_ROOTS: tuple[str, ...] = (".claude/skills", ".agents/skills")
_NAME_LINE_RE = re.compile(r"^name:[ \t]*.*$", re.MULTILINE)


def mirror_name(skill_name: str) -> str:
    return f"{MIRROR_PREFIX}{skill_name}"


def generated_header(skill_name: str) -> str:
    return f"<!-- GENERATED from skills/{skill_name}/SKILL.md; do not edit -->"


def render_mirror(source_text: str, skill_name: str) -> str:
    """Render the mirror text: same front matter with a prefixed ``name``, then the header.

    The YAML is rewritten textually (only the top-level ``name:`` line) so the rest of the
    front matter is byte-identical to the source. Line endings are normalised to ``\\n``.
    """
    text = source_text.replace("\r\n", "\n")
    raw, data, body = split_front_matter(text)
    if data.get("name") != skill_name:
        raise ValueError(f"source name {data.get('name')!r} != {skill_name!r}")
    new_raw, count = _NAME_LINE_RE.subn(f"name: {mirror_name(skill_name)}", raw, count=1)
    if count != 1:  # pragma: no cover - guarded by split_front_matter + name check
        raise ValueError("front matter has no top-level 'name:' line")
    return f"---\n{new_raw}\n---\n{generated_header(skill_name)}\n{body.lstrip(chr(10))}"


@dataclass(frozen=True)
class MirrorDrift:
    path: str
    reason: str  # missing | stale | orphan


def expected_mirrors(root: Path) -> dict[Path, str]:
    out: dict[Path, str] = {}
    for src in discover_skill_files(root):
        name = src.parent.name
        text = render_mirror(src.read_text(encoding="utf-8"), name)
        for mroot in MIRROR_ROOTS:
            out[root / mroot / mirror_name(name) / "SKILL.md"] = text
    return out


def check_mirrors(root: Path) -> list[MirrorDrift]:
    """Return drift between sources and mirrors (empty list = in sync)."""
    drift: list[MirrorDrift] = []
    expected = expected_mirrors(root)
    for path, text in sorted(expected.items()):
        rel = path.relative_to(root).as_posix()
        if not path.is_file():
            drift.append(MirrorDrift(rel, "missing"))
        elif path.read_text(encoding="utf-8").replace("\r\n", "\n") != text:
            drift.append(MirrorDrift(rel, "stale"))
    for d in drift_orphans(root, expected):
        drift.append(MirrorDrift((d / "SKILL.md").relative_to(root).as_posix(), "orphan"))
    return drift


def sync_mirrors(root: Path) -> list[str]:
    """Write all mirrors and delete orphaned ``sparkforge-azure-*`` mirrors. Returns changes."""
    changed: list[str] = []
    expected = expected_mirrors(root)
    for path, text in sorted(expected.items()):
        current = path.read_text(encoding="utf-8") if path.is_file() else None
        if current != text:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(text.encode("utf-8"))
            changed.append(path.relative_to(root).as_posix())
    for d in drift_orphans(root, expected):
        f = d / "SKILL.md"
        if f.is_file():
            f.unlink()
        if d.is_dir() and not any(d.iterdir()):
            d.rmdir()
        changed.append(f.relative_to(root).as_posix())
    return changed


def drift_orphans(root: Path, expected: dict[Path, str]) -> list[Path]:
    out: list[Path] = []
    for mroot in MIRROR_ROOTS:
        base = root / mroot
        if base.is_dir():
            for d in sorted(base.iterdir()):
                ours = d.is_dir() and d.name.startswith(MIRROR_PREFIX)
                if ours and d / "SKILL.md" not in expected:
                    out.append(d)
    return out
