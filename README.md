# Catpilot Security Skills

<p align="left">
  <img src="assets/catpilot-logo.png" alt="Catpilot" width="100" style="vertical-align: middle;">
  <em>Paws before you push.</em>
</p>

![Release](https://img.shields.io/badge/release-2026.05.06-blue) ![License](https://img.shields.io/badge/license-MIT-green) ![Format](https://img.shields.io/badge/format-Anthropic%20Agent%20Skills-7B3FE4)

Security skills for AI coding agents — installable into Claude Code, Cursor, Codex, OpenClaw, Cline, Aider, GitHub Copilot, OpenCode, and 40+ other agents with one command.

Born from a real incident where an agent wiped production environment variables with a partial YAML update. The rules in this repo come from incidents like that one — battle-tested, dogfooded daily at [Catpilot.ai](https://catpilot.ai), MIT-licensed.

## Install

```bash
npx skills add catpilotai/catpilot-ai-guardrails --skill catpilot-security-core
```

That's it. Your coding agent now follows the security rules.

This uses the [skills.sh CLI](https://skills.sh) (`vercel-labs/skills`), which copies `catpilot-security-core/SKILL.md` into the right place for your agent (e.g. `~/.claude/skills/`, `.cursor/rules/`, `~/.codex/skills/`, …). 51+ runtimes supported.

## What's in the box

`catpilot-security-core` (~26 KB) — the always-on baseline. Apply it on every code generation, file write, and shell command:

| Component | Catches |
|---|---|
| **secret-blocking** | Hardcoded API keys, tokens, passwords, private keys, OAuth secrets, JWT signing keys, database URLs with embedded credentials. |
| **cloud-cli-safety** | Partial-YAML resets (Azure, AWS, GCP), `terraform apply -auto-approve` against prod state, `kubectl delete namespace`, `helm upgrade` without diff, recursive S3 deletes — every cloud command goes through the universal six-step protocol. |

Each component carries control mappings for **SOC 2, PCI-DSS, ISO 27001, NIST CSF, and OWASP Top 10**, with severity, evidence patterns, and worked negative examples (real incidents, masked).

More components and framework extensions land in subsequent releases.

## Format

Skills use the [Anthropic Agent Skills](https://agentskills.io/specification) format exactly. A skill is a directory containing a `SKILL.md` file with YAML frontmatter and a markdown body. Catpilot extensions (severity, control mappings, applies-to, evidence patterns) live under `metadata.catpilot.*`, which other runtimes ignore.

This means: anywhere `npx skills add` works, Catpilot skills work. Anywhere it doesn't, you can copy the directory in by hand and your agent will read it.

## Other ways to install

```bash
# Install globally so every project picks it up
npx skills add catpilotai/catpilot-ai-guardrails --skill catpilot-security-core --global

# Pick a specific agent (skills.sh defaults to detecting installed agents)
npx skills add catpilotai/catpilot-ai-guardrails --skill catpilot-security-core --agent cursor

# List what's available without installing
npx skills add catpilotai/catpilot-ai-guardrails --list

# Or skip the CLI entirely — just copy the skill in by hand
git clone https://github.com/catpilotai/catpilot-ai-guardrails.git
cp -r catpilot-ai-guardrails/skills/catpilot-security-core ~/.claude/skills/
```

## Versioning

- **Releases** are CalVer (`YYYY.MM.DD`). Current release: **`2026.05.06`**.
- **Source skill components** inside a release are semver — `secret-blocking@1.0.0`, `cloud-cli-safety@1.0.0`. The release frontmatter records which versions of which components shipped.

CalVer matches the cadence of a content repo: each release is a dated snapshot, and the date is the meaningful signal for users and auditors. Semver on individual components carries the breaking-change semantics that matter for downstream consumers.

## How it's built

```
src/skills/             # source components (semver, edited by hand)
  core/
    bundle.toml         # tier config: name, version, description
    secret-blocking/
      SKILL.md          # one component
    cloud-cli-safety/
      SKILL.md
skills/                 # shipped bundles (CalVer, generated)
  catpilot-security-core/
    SKILL.md            # what `npx skills add` installs
tools/
  bundle.py             # deterministic bundler
docs/spec/              # format spec, packaging spec, V2 postmortem
```

`tools/bundle.py` reads source components, aggregates frontmatter (severity = max, control mappings = sorted union, `applies_to` = union with `any` collapse), concatenates bodies in lexicographic order, and writes the shipped bundle. CI runs `python tools/bundle.py --check` on every PR — if `skills/` drifts from `src/skills/`, the build fails with a unified diff.

## Contributing

PRs welcome — propose a new rule, fix a false positive, add a control mapping, port a v2.x rule into a source skill.

- Read [`docs/spec/SKILL_FORMAT.md`](./docs/spec/SKILL_FORMAT.md) for the frontmatter shape.
- Read [`docs/spec/PACKAGING.md`](./docs/spec/PACKAGING.md) for tier conventions and bundler aggregation rules.
- Run `python tools/bundle.py` before pushing; the CI gate is strict.
- See [`CONTRIBUTING.md`](./CONTRIBUTING.md) for the rest.

## Roadmap

| Tier | Bundle | Status |
|---|---|---|
| Core (always-on) | `catpilot-security-core` | shipped (2 components, 5 more queued) |
| Framework extensions | `catpilot-django-security`, `catpilot-fastapi-security`, `catpilot-rails-security`, `catpilot-express-security`, `catpilot-nextjs-security`, `catpilot-springboot-security`, `catpilot-docker-security` | planned (content exists in `frameworks/`, migrating into source skills) |
| Advanced (multi-agent / opt-in) | `catpilot-security-advanced` | planned |

Validator (`tools/validate-skill.py`) and framework-detection helper (`tools/recommend.py`) follow.

## Migrating from v2.x

If you're on a v2.x install (`git submodule add … && ./setup.sh`), the v2 files in this repo (`copilot-instructions.md`, `FULL_GUARDRAILS.md`, `setup.sh`, `frameworks/*`) still work — they're soft-deprecated, not removed. New installs should use the skills.sh path above. Migration guide lands as those files are ported into the new source-skills layout.

## License

MIT. See [LICENSE](./LICENSE).

## Security

Found something dangerous? See [SECURITY.md](./SECURITY.md). For specific vulnerabilities, email **hi@catpilot.ai**.
