# v3.0 Spec — Index

**Status:** Draft for review (PR #2).
**Branch:** `v3-spec-skillsh`.
**Scope:** Realign the v3.0 spec to the [Anthropic Agent Skills](https://agentskills.io/specification) format and the [skills.sh](https://skills.sh) distribution channel.

---

## Why this PR exists

PR #1 landed a v3.0 spec built around a `<name>.skill.md` flat-file format and a custom installer. Investigating skills.sh revealed two things:

1. The Anthropic Agent Skills format — directories named `<skill-name>/` containing a `SKILL.md` file plus optional `scripts/`, `references/`, `assets/` — is the de facto ecosystem standard. 51+ AI coding agents already install skills in that shape via `npx skills add`.
2. Catpilot ships a custom installer ⇒ we maintain a 51-runtime install matrix forever. Catpilot ships in the standard shape ⇒ existing tooling handles every runtime for free, and our skills appear on the public skills.sh leaderboard.

PR #2 is the realignment. The strategic decisions from PR #1 (3-tier bundling, source-vs-shipped split, zero phone-home OSS) are unchanged. The file format and distribution path are the things that change.

## What's in this PR

| File | Purpose |
|---|---|
| [`docs/v3-spec/SKILL_FORMAT.md`](./SKILL_FORMAT.md) | Rewritten. Catpilot skills are valid Anthropic Agent Skills. Catpilot extensions live under `metadata.catpilot.*`. Validation rules and the severity scale are preserved from PR #1. |
| [`docs/v3-spec/PACKAGING.md`](./PACKAGING.md) | Rewritten. Three tiers, bundler mechanics, deterministic output, distribution via `npx skills add`. The custom installer is dropped. |
| [`docs/v3-spec/V2_DIAGNOSTIC.md`](./V2_DIAGNOSTIC.md) | Unchanged. |
| [`docs/v3-spec/README.md`](./README.md) | This file. |
| [`src/skills/core/secret-blocking/SKILL.md`](../../src/skills/core/secret-blocking/SKILL.md) | Migrated worked example. Same content as PR #1; new layout (directory + `SKILL.md`) and new frontmatter (`metadata.catpilot.*` instead of top-level `catpilot:`). |
| [`src/skills/core/cloud-cli-safety/SKILL.md`](../../src/skills/core/cloud-cli-safety/SKILL.md) | Same as above. |

The deleted files from PR #1 (`skills/source/core/*.skill.md`) appear in the diff as removals — they have been replaced by the new layout under `src/skills/core/<name>/SKILL.md`.

## Architectural decisions — current state

Decisions from PR #1, with their status under PR #2:

| # | Decision | Status | PR #2 change |
|---|---|---|---|
| 1 | OSS is zero-phone-home | LOCKED | unchanged |
| 2 | SaaS uses event collector under commercial agreement (out of scope for OSS) | LOCKED | unchanged |
| 3 | Catpilot skills are Anthropic Agent Skill superset | LOCKED | unchanged in spirit; **conformance now exact**, not "superset" |
| 4 | File extension `.skill.md` | **REVERSED** | Now: directory `<skill-name>/` + `SKILL.md` (Anthropic spec). Catpilot does not invent a new extension. |
| 5 | Severity scale critical/high/medium/low/info | LOCKED | unchanged |
| 6 | Control mappings: SOC2, PCI-DSS, ISO 27001, NIST CSF, OWASP | LOCKED | unchanged |
| 7 | 3-tier packaging (core / framework extensions / advanced) | LOCKED | unchanged |
| 8 | Source under `skills/source/<tier>/`, bundles under `skills/dist/` | **AMENDED** | Now: source under `src/skills/<tier>/<name>/SKILL.md` (outside `skills/`, ignored by skills.sh CLI). Bundles under `skills/<bundle-name>/SKILL.md` (visible to skills.sh CLI). |
| 9 | Bundle frontmatter records per-component versions | LOCKED | unchanged; now lives under `metadata.catpilot.bundle.components[]` |
| 10 | Bundler aggregates severity (max), control mappings (union) | LOCKED | unchanged |
| 11 | Install distribution path | **LOCKED in this PR** | `npx skills add ToomeSauce/catpilot-ai-guardrails`. No custom installer. |
| 12 | Tier 3 naming: `advanced` vs `agentic` | **LOCKED** | `advanced`. |
| 13 | Compliance set additions (HIPAA / GDPR for v3.0?) | **LOCKED** | Keep v3.0 tight: SOC2, PCI-DSS, ISO 27001, NIST CSF, OWASP. HIPAA/GDPR in v3.1. |
| 14 | Bundler implementation language | **LOCKED** | Python (matches Catpilot stack). |
| 15 | Validator implementation | OPEN | Will be Python. Tracking issue follows. |
| 16 | Migration of remaining v2.x rule categories to source skills | OPEN | Tracked. Plan: 7 more core skills, framework extensions, advanced tier. |
| 17 | Launch motion (blog, HN, etc.) | OPEN | Recommendation in `V2_DIAGNOSTIC.md`. |

## Reading order for review (~25 min)

1. **This file** — context for why PR #2 exists (3 min).
2. **`PACKAGING.md`** — three tiers, bundler aggregation rules, distribution via skills.sh (8 min).
3. **`SKILL_FORMAT.md`** — frontmatter shape, validation rules, body conventions (12 min).
4. **`src/skills/core/secret-blocking/SKILL.md`** — sanity-check the format on real content (2 min).

## What this PR is not

- Not the bundler. (Specified in PACKAGING §3–5; implementation is a follow-up PR.)
- Not the validator. (Specified in SKILL_FORMAT §6; implementation is a follow-up PR.)
- Not new content. The two source skills are migrated 1:1 from PR #1; only the layout and frontmatter change.
- Not a new README on main. v2.x README stays put until v3.0-rc.
- Not a v3.0 release.
