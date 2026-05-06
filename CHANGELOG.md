# Changelog

All notable changes to this project will be documented in this file.

Releases from `2026.05.06` forward use [CalVer](https://calver.org) (`YYYY.MM.DD`). Source-skill components inside each release continue to use [SemVer](https://semver.org).

## [2026.05.06] — 2026-05-06

### Changed

- **Repo realigned to the [Anthropic Agent Skills](https://agentskills.io/specification) format.** Skills are now directories named `<skill>/` containing a `SKILL.md` file with YAML frontmatter, exactly matching the Anthropic spec. Catpilot-specific extensions live under `metadata.catpilot.*`, which other runtimes ignore.
- **Distribution moved to [skills.sh](https://skills.sh) (`vercel-labs/skills`).** The new install command is `npx skills add catpilotai/catpilot-ai-guardrails --skill catpilot-security-core`. 51+ AI coding agents supported (Claude Code, Cursor, Codex, OpenClaw, Cline, Aider, GitHub Copilot, OpenCode, etc.).
- **Versioning split.** Releases are CalVer (`YYYY.MM.DD`); source-skill components stay semver. The bundler validates both regimes.

### Added

- **`catpilot-security-core` bundle** — the always-on security baseline. Two components shipping in this release:
  - `secret-blocking@1.0.0` — hardcoded secrets, API keys, tokens, OAuth credentials, JWT signing keys, DB URLs with embedded creds.
  - `cloud-cli-safety@1.0.0` — partial-YAML resets, `terraform apply -auto-approve`, `kubectl delete namespace`, recursive S3 deletes, the universal six-step protocol for any cloud-modifying command.
- **Spec docs** under `docs/spec/`: `SKILL_FORMAT.md` (frontmatter shape, validation, severity scale, body conventions), `PACKAGING.md` (three tiers, bundler mechanics, distribution), `V2_DIAGNOSTIC.md` (one-page postmortem on v2.x distribution).
- **Deterministic bundler** at `tools/bundle.py` (~370 LOC, Python 3.11+). Aggregates severity (max), control mappings (sorted union), `applies_to` (union with `any` collapse). CalVer-validated bundle versions, semver-validated component versions.
- **CI gate** at `.github/workflows/bundle-check.yml`. Runs `python tools/bundle.py --check` on every PR; fails with a unified diff if `skills/` drifts from `src/skills/`.
- **Three packaging tiers** locked: `catpilot-security-core` (always-on), `catpilot-<framework>-security` (per-framework extensions), `catpilot-security-advanced` (multi-agent / opt-in). Only core ships in this release; the other two are planned.
- **Compliance set** locked: SOC 2, PCI-DSS, ISO 27001, NIST CSF, OWASP Top 10. HIPAA and GDPR follow in a later release.

### Deprecated

- **Submodule + bash installer (`setup.sh`)** — still works for v2.x users, but the new install path is `npx skills add`. The script will print a deprecation notice when run.
- **`copilot-instructions.md` and `FULL_GUARDRAILS.md`** — monolithic v2.x rule files. Their content is being migrated into per-concern source skills under `src/skills/`. Files remain on `main` until the migration completes.
- **`frameworks/*` directories** — v2.x framework patterns (`FULL_*.md` + `condensed.md`). Migrating into `src/skills/<framework>/` extension skills as part of the next release cadence.

### Architectural decisions locked

- OSS = zero phone-home, ever. No telemetry, no crash reports, no anonymous events. SaaS-side dynamic skill updates are a separate workstream under commercial agreement.
- Conformance: exact Anthropic Agent Skills, not "superset."
- Tier 3 name: `catpilot-security-advanced` (not `agentic`).
- Distribution: `npx skills add catpilotai/catpilot-ai-guardrails`. No custom installer.
- Bundler implementation language: Python.

## [2.1.0] — 2026-03-06

### Added

- **Agentic framework: Scheduled Task (Cron) Security** — guardrails for unsupervised cron/scheduled agent sessions: timeout enforcement, lightweight model selection, read-only tool scoping, no self-modifying schedules, token budget auditing
- **Agentic framework: Agent Identity Integrity** — file hash checksums at session start, human notification on SOUL.md/AGENTS.md modification, version control for behavioral files, distinguishing self-improvement from constraint drift
- **Agentic framework: Multi-Agent Authentication & Authorization** — token-authenticated inter-agent communication, agent allowlists, message provenance tracking, ping-pong depth caps, privilege escalation prevention, audit logging for all inter-agent traffic
- **Condensed agentic rules** updated with cron security, identity integrity, and inter-agent auth summaries

### Context

These additions address three security gaps identified through community research (Moltbook agent security discussions):
1. Cron jobs as unsupervised root access (inspired by Hazel_OC's analysis)
2. Agent identity drift via self-modification of behavioral files (inspired by Hazel_OC's SOUL.md diff experiment)
3. Multi-agent permission escalation risks as agent teams scale (inspired by eudaemon_0's supply chain work and real-world multi-agent deployments)

## [2.0.1] — 2026-02-06

### Fixed

- **OpenClaw framework**: Allow `.env` files (with `.gitignore` requirement) instead of blanket-banning all plaintext secret storage
- **OpenClaw framework**: Replace shell profile (`~/.zshrc`) secret export pattern with `.env` + `.gitignore` pattern
- **OpenClaw framework**: Replace non-existent `SOUL.md`/`TOOLS.md` references with actual repo files (`CLAUDE.md`, `openclaw.json`, `~/.openclaw/`)

## [2.0.0] — 2026-02-06

### Added

- **AI Agent & Tool Safety** — prompt injection defense, credential isolation, gateway binding rules, skill/plugin sandboxing
- **Supply Chain Security** — skill marketplace vetting checklist, typosquatting detection, red flag patterns (base64 payloads, external downloads, category flooding)
- **File & Credential Permissions** — owner-only rules for `~/.ssh/`, `~/.aws/`, `~/.openclaw/`, `~/.config/gcloud/`, `~/.kube/`
- **Incident Response** — 5-step playbook: rotate, audit, purge git history, check persistence, assess blast radius
- **CI/CD Pipeline Safety** — pin GitHub Actions to SHA, minimal permissions, OIDC over long-lived secrets, approval gates for production
- **TypeScript framework** — `eval`/`new Function()` blocking, `child_process` safety, prototype pollution, path traversal, ReDoS, Zod validation patterns
- **OpenClaw framework** — gateway binding, ClawHub skill vetting, sandbox configuration, DM policy, prompt injection defense, credential storage
- **Agentic AI framework** — tool sandboxing, human-in-the-loop, memory isolation, output filtering, multi-agent coordination, rate limiting, credential management
- **`--verify` flag** for `setup.sh` — checks installed guardrails version matches source
- **OpenClaw detection** in `setup.sh` — auto-detects `openclaw.mjs`, `.openclaw/`, or OpenClaw references in `AGENTS.md`
- **Agentic AI detection** in `setup.sh` — auto-detects LangChain, CrewAI, AutoGPT, LangGraph, LlamaIndex in dependencies
- **TypeScript detection** in `setup.sh` — auto-detects `tsconfig.json` (when not Next.js)
- **OpenClaw** added to Tool Support (auto-configures `AGENTS.md` symlink)

### Changed

- **Local CLI Safety** expanded — added gateway/control port exposure and `0.0.0.0` binding rules
- **Version** bumped across all files: `copilot-instructions.md`, `FULL_GUARDRAILS.md`, README, and all 8 framework `FULL_*.md` files
- **"What It Catches"** list expanded from 8 to 13 categories
- **Framework detection table** updated with TypeScript and OpenClaw entries
- **Files table** expanded with all 10 framework names

## [1.0.0] — 2025-06-15

### Added

- Initial release
- Cloud CLI safety rules (Azure, AWS, GCP) — query-before-modify pattern
- Secret detection — 40+ patterns (Stripe, AWS, GitHub, OpenAI, Anthropic, Slack, Google, SendGrid, private keys, connection strings)
- Database safety — transactions, previews, no DELETE/UPDATE without WHERE
- Terraform/IaC — plan before apply, no `-auto-approve`
- Kubernetes/Helm — dry-run and diff before applying
- Git safety — no force-push to protected branches
- Secure coding — OWASP Top 10 (SQL injection, XSS, command injection, path traversal, deserialization)
- PII & test data rules — faker libraries, `example.com`, test credit card numbers
- Python security — no `shell=True`, no `pickle.loads()` on untrusted data
- Docker safety — pinned digests, non-root user, build secrets
- Two-tier architecture: condensed `copilot-instructions.md` (~4KB) + `FULL_GUARDRAILS.md` (~20KB)
- `setup.sh` with auto-detection for 8 frameworks (Next.js, Django, Rails, FastAPI, Spring Boot, Express, Python, Docker)
- Multi-tool support: VS Code, Cursor, Windsurf, JetBrains, Claude Code, Cline, Aider, Codex CLI
- Framework-specific security patterns for all 8 frameworks
