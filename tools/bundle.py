"""Catpilot v3.0 skill bundler.

Reads source skills under src/skills/<tier>/<name>/SKILL.md and produces
shipped bundles at skills/<bundle-name>/SKILL.md, in the Anthropic Agent
Skills format expected by `npx skills add`.

Determinism rules (PACKAGING.md §5):
  1. Components are emitted in lexicographic order by metadata.catpilot.id.
  2. List-valued aggregations are sorted alphabetically and deduplicated.
  3. Frontmatter key order is fixed by KEY_ORDER below.
  4. Output uses LF line endings exclusively.
  5. No timestamps appear in output.

Run with --check to re-bundle and diff against the committed skills/ tree
(used in CI to enforce that skills/ is the deterministic output of src/).

Usage:
  python tools/bundle.py                # build all tiers
  python tools/bundle.py --tier core    # build a single tier
  python tools/bundle.py --check        # CI mode: verify skills/ is up to date
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import re
import shutil
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = REPO_ROOT / "src" / "skills"
DIST_ROOT = REPO_ROOT / "skills"

SEVERITY_ORDER = ["info", "low", "medium", "high", "critical"]

# Anthropic spec name regex: 1-64 chars, lowercase a-z + digits + hyphens,
# no leading/trailing/consecutive hyphens.
NAME_RE = re.compile(r"^[a-z0-9](?:[a-z0-9]|-(?!-))*[a-z0-9]$|^[a-z0-9]$")
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")

# Stable frontmatter key order. Anything not listed appears after, sorted.
TOP_KEY_ORDER = ["name", "description", "license", "compatibility", "metadata"]
CATPILOT_KEY_ORDER = [
    "bundle",
    "severity",
    "category",
    "applies_to",
    "control_mappings",
    "provenance",
    "maintainers",
    "references",
]
BUNDLE_KEY_ORDER = ["name", "version", "tier", "components"]


@dataclass
class SourceSkill:
    path: Path
    frontmatter: dict
    body: str

    @property
    def cp(self) -> dict:
        return self.frontmatter.get("metadata", {}).get("catpilot", {})

    @property
    def id(self) -> str:
        return self.cp.get("id") or self.frontmatter.get("name", "")

    @property
    def version(self) -> str:
        return self.cp.get("version", "0.0.0")

    @property
    def severity(self) -> str:
        return self.cp.get("severity", "medium")


# --------------------------------------------------------------------------
# Parsing


def split_frontmatter(text: str) -> tuple[dict, str]:
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.DOTALL)
    if not m:
        raise ValueError("missing YAML frontmatter")
    return yaml.safe_load(m.group(1)) or {}, m.group(2)


def load_source_skill(skill_dir: Path) -> SourceSkill:
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        raise FileNotFoundError(f"no SKILL.md at {skill_md}")
    fm, body = split_frontmatter(skill_md.read_text())
    skill = SourceSkill(path=skill_dir, frontmatter=fm, body=body)
    validate_source_skill(skill)
    return skill


def validate_source_skill(skill: SourceSkill) -> None:
    fm = skill.frontmatter
    name = fm.get("name")
    if not name:
        raise ValueError(f"{skill.path}: frontmatter missing 'name'")
    if not NAME_RE.match(name):
        raise ValueError(f"{skill.path}: 'name' {name!r} fails Anthropic spec regex")
    if name != skill.path.name:
        raise ValueError(
            f"{skill.path}: directory name {skill.path.name!r} != frontmatter name {name!r}"
        )
    desc = fm.get("description")
    if not desc or len(desc) > 1024:
        raise ValueError(f"{skill.path}: 'description' missing or >1024 chars")
    if not fm.get("license"):
        raise ValueError(f"{skill.path}: Catpilot requires 'license'")
    cp = skill.cp
    if not cp:
        raise ValueError(f"{skill.path}: missing metadata.catpilot block")
    if cp.get("id") != name:
        raise ValueError(
            f"{skill.path}: metadata.catpilot.id {cp.get('id')!r} != name {name!r}"
        )
    if not SEMVER_RE.match(skill.version):
        raise ValueError(f"{skill.path}: invalid semver {skill.version!r}")
    if skill.severity not in SEVERITY_ORDER:
        raise ValueError(f"{skill.path}: bad severity {skill.severity!r}")
    if not cp.get("category"):
        raise ValueError(f"{skill.path}: metadata.catpilot.category required")


# --------------------------------------------------------------------------
# Aggregation


def max_severity(severities: list[str]) -> str:
    return max(severities, key=lambda s: SEVERITY_ORDER.index(s))


def union_sorted(items: list[list[str]]) -> list[str]:
    seen: set[str] = set()
    for sub in items:
        for x in sub or []:
            seen.add(str(x))
    return sorted(seen)


def collapse_any(values: list[str]) -> list[str]:
    """If 'any' appears anywhere, the result is just ['any']."""
    if "any" in values:
        return ["any"]
    return values


def aggregate_applies_to(skills: list[SourceSkill]) -> dict:
    langs = union_sorted([s.cp.get("applies_to", {}).get("languages", []) for s in skills])
    fws = union_sorted([s.cp.get("applies_to", {}).get("frameworks", []) for s in skills])
    runtimes = union_sorted([s.cp.get("applies_to", {}).get("runtimes", []) for s in skills])
    return {
        "languages": collapse_any(langs),
        "frameworks": collapse_any(fws),
        "runtimes": runtimes,
    }


def aggregate_control_mappings(skills: list[SourceSkill]) -> dict:
    frameworks = ["soc2", "pci_dss", "iso_27001", "nist_csf", "owasp_top_10"]
    out = {}
    for fw in frameworks:
        merged = union_sorted(
            [s.cp.get("control_mappings", {}).get(fw, []) for s in skills]
        )
        if merged:
            out[fw] = merged
    return out


# --------------------------------------------------------------------------
# Emission


def order_dict(d: dict, order: list[str]) -> dict:
    """Return a new dict with keys in the given order, then any extras sorted."""
    out: dict = {}
    for k in order:
        if k in d:
            out[k] = d[k]
    for k in sorted(d.keys()):
        if k not in out:
            out[k] = d[k]
    return out


class FlowList(list):
    """List that yaml.dump emits in flow style ([a, b, c])."""


def _flow_list_representer(dumper, data):
    return dumper.represent_sequence("tag:yaml.org,2002:seq", data, flow_style=True)


yaml.add_representer(FlowList, _flow_list_representer)


def dump_yaml(d: dict) -> str:
    # Ensure deterministic ordering at every level we care about.
    return yaml.dump(d, sort_keys=False, allow_unicode=True, width=10_000, default_flow_style=False)


def build_bundle_frontmatter(
    bundle_name: str,
    bundle_cfg: dict,
    skills: list[SourceSkill],
) -> dict:
    components = [
        {"id": s.id, "version": s.version} for s in sorted(skills, key=lambda s: s.id)
    ]
    cp = {
        "bundle": order_dict(
            {
                "name": bundle_name,
                "version": bundle_cfg["version"],
                "tier": bundle_cfg["tier"],
                "components": components,
            },
            BUNDLE_KEY_ORDER,
        ),
        "severity": max_severity([s.severity for s in skills]),
        "category": bundle_cfg.get("category", "security"),
        "applies_to": aggregate_applies_to(skills),
        "control_mappings": aggregate_control_mappings(skills),
        "provenance": {
            "origin": "catpilot",
            "incident_derived": any(
                s.cp.get("provenance", {}).get("incident_derived") for s in skills
            ),
        },
        "maintainers": [{"team": "catpilot-security"}],
    }
    cp = order_dict(cp, CATPILOT_KEY_ORDER)

    fm = {
        "name": bundle_name,
        "description": bundle_cfg["description"].strip().replace("\n", " "),
        "license": "MIT",
        "metadata": {"catpilot": cp},
    }
    return order_dict(fm, TOP_KEY_ORDER)


def build_bundle_body(bundle_cfg: dict, skills: list[SourceSkill]) -> str:
    parts = [bundle_cfg["preamble"].strip(), ""]
    for s in sorted(skills, key=lambda s: s.id):
        parts.append("---")
        parts.append("")
        parts.append(f"## {s.id}")
        parts.append("")
        # Strip a leading H1 if present in component body (none expected today).
        body = s.body.lstrip("\n")
        # Demote any H1/H2 inside component bodies by one level so the
        # bundle's H2 component heading stays the highest within the section.
        # Component bodies today start at H2 ("## Why", "## Rules"), so we
        # demote them to H3 within the bundle.
        body = _demote_headings(body)
        parts.append(body.rstrip())
        parts.append("")
    return "\n".join(parts).rstrip() + "\n"


_FENCE_RE = re.compile(r"^(```|~~~)")
_HEADING_RE = re.compile(r"^(#{1,5}) \S")


def _demote_headings(md: str) -> str:
    """Add one '#' to every ATX heading so component H2 -> H3 inside bundle.

    Skips lines inside fenced code blocks so '# bash comments' aren't mangled.
    """
    out = []
    in_fence = False
    for line in md.split("\n"):
        m = _FENCE_RE.match(line)
        if m:
            in_fence = not in_fence
            out.append(line)
            continue
        if not in_fence and _HEADING_RE.match(line):
            out.append("#" + line)
        else:
            out.append(line)
    return "\n".join(out)


def render_skill_md(frontmatter: dict, body: str) -> str:
    return "---\n" + dump_yaml(frontmatter) + "---\n\n" + body.lstrip("\n")


# --------------------------------------------------------------------------
# Companion files


COMPANION_DIRS = ("references", "scripts", "assets")


def copy_companions(src_skill: Path, dst_bundle: Path, namespace: str) -> None:
    for d in COMPANION_DIRS:
        src = src_skill / d
        if not src.is_dir():
            continue
        dst = dst_bundle / d / namespace
        if dst.exists():
            shutil.rmtree(dst)
        dst.mkdir(parents=True)
        for item in sorted(src.rglob("*")):
            if item.is_file():
                rel = item.relative_to(src)
                target = dst / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(item.read_bytes())


# --------------------------------------------------------------------------
# Tier orchestration


def discover_tiers() -> list[Path]:
    """Return tier directories under src/skills/ that contain a bundle.toml."""
    out = []
    for child in sorted(SRC_ROOT.iterdir()):
        if not child.is_dir():
            continue
        if (child / "bundle.toml").is_file():
            out.append(child)
        # frameworks/ has nested bundle.tomls.
        if child.name == "frameworks":
            for fw in sorted(child.iterdir()):
                if fw.is_dir() and (fw / "bundle.toml").is_file():
                    out.append(fw)
    return out


def load_bundle_cfg(tier_dir: Path) -> dict:
    return tomllib.loads((tier_dir / "bundle.toml").read_text())["bundle"]


def build_tier(tier_dir: Path, dist_root: Path) -> Path:
    cfg = load_bundle_cfg(tier_dir)
    bundle_name = cfg["name"]
    skill_dirs = sorted(d for d in tier_dir.iterdir() if d.is_dir())
    skills = [load_source_skill(d) for d in skill_dirs]
    if not skills:
        raise ValueError(f"{tier_dir}: no source skills found")

    fm = build_bundle_frontmatter(bundle_name, cfg, skills)
    body = build_bundle_body(cfg, skills)
    rendered = render_skill_md(fm, body)

    bundle_dir = dist_root / bundle_name
    if bundle_dir.exists():
        shutil.rmtree(bundle_dir)
    bundle_dir.mkdir(parents=True)
    (bundle_dir / "SKILL.md").write_text(rendered)

    for s in skills:
        copy_companions(s.path, bundle_dir, namespace=s.id)

    return bundle_dir


# --------------------------------------------------------------------------
# CLI


def cmd_build(tier_filter: str | None) -> int:
    tiers = discover_tiers()
    if tier_filter:
        tiers = [t for t in tiers if t.name == tier_filter]
        if not tiers:
            print(f"no tier matched {tier_filter!r}", file=sys.stderr)
            return 2
    for tier in tiers:
        out = build_tier(tier, DIST_ROOT)
        print(f"built {out.relative_to(REPO_ROOT)}")
    return 0


def _hash_tree(root: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not root.exists():
        return out
    for p in sorted(root.rglob("*")):
        if p.is_file():
            rel = str(p.relative_to(root))
            out[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def cmd_check() -> int:
    snapshot_before = _hash_tree(DIST_ROOT)
    # Build into a scratch dir so we don't mutate skills/ on a check run.
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        scratch = Path(tmp) / "skills"
        scratch.mkdir()
        for tier in discover_tiers():
            build_tier(tier, scratch)
        snapshot_after = _hash_tree(scratch)

    drift = []
    all_keys = sorted(set(snapshot_before) | set(snapshot_after))
    for k in all_keys:
        a = snapshot_before.get(k)
        b = snapshot_after.get(k)
        if a != b:
            drift.append((k, a, b))

    if not drift:
        print("OK: skills/ matches src/skills/ deterministic output")
        return 0

    print("DRIFT: skills/ does not match src/skills/ deterministic output", file=sys.stderr)
    for k, a, b in drift:
        if a is None:
            print(f"  + {k}  (missing in skills/)", file=sys.stderr)
        elif b is None:
            print(f"  - {k}  (extra in skills/)", file=sys.stderr)
        else:
            print(f"  ~ {k}  (content differs)", file=sys.stderr)
            # Print a small diff for SKILL.md drift.
            if k.endswith("SKILL.md"):
                committed = (DIST_ROOT / k).read_text().splitlines()
                with tempfile.TemporaryDirectory() as tmp:
                    scratch = Path(tmp) / "skills"
                    scratch.mkdir()
                    for tier in discover_tiers():
                        build_tier(tier, scratch)
                    fresh = (scratch / k).read_text().splitlines()
                diff = difflib.unified_diff(
                    committed, fresh, fromfile=f"a/{k}", tofile=f"b/{k}", lineterm=""
                )
                for line in list(diff)[:60]:
                    print("    " + line, file=sys.stderr)
    print("\nRebuild locally with:  python tools/bundle.py", file=sys.stderr)
    return 1


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="bundle.py", description="Catpilot v3.0 skill bundler")
    p.add_argument("--tier", help="build only this tier (matches src/skills/<tier> dir name)")
    p.add_argument("--check", action="store_true", help="verify skills/ is up to date with src/")
    args = p.parse_args(argv)
    if args.check:
        return cmd_check()
    return cmd_build(args.tier)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
