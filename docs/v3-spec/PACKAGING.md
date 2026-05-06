# v3.0 Packaging Strategy — How Skills Are Bundled and Installed

**Status:** Draft for review
**Audience:** Maintainers and contributors deciding what end users install
**Companion to:** [`SKILL_FORMAT.md`](./SKILL_FORMAT.md) (file-level format) and [`V2_DIAGNOSTIC.md`](./V2_DIAGNOSTIC.md) (why v2.x didn't land)

---

## 1. The decision this doc makes

Authoring granularity and install granularity are **decoupled** in v3.0:

- **Authoring unit:** one source skill per concern (~9 for core, ~7 framework extensions, ~4 advanced). Lives under `skills/source/`. Independently versioned.
- **Install unit:** **3 tiers**, each shipping as a single bundle skill under `skills/dist/`. End users install one tier per profile.

Source skills are the unit of diffs, reviews, and SaaS-side updates. Bundle skills are the unit of install. The bundler joins them; see `SKILL_FORMAT.md` §7 for the file-level mechanics.

---

## 2. Why decoupling matters

### 2.1 Atomic install would replicate v2.x's adoption tax

`V2_DIAGNOSTIC.md` identifies install friction as the load-bearing reason v2.x sat at zero stars. Asking a developer to install 13+ separate skills — even via `npx` — recreates that friction in a new wrapper. Asking them to *decide which 13 of 30 they want* is worse: the decision burden lands on the person least equipped to make it (someone who showed up looking for "basic AI coding security" and now has to read 30 READMEs).

Modern competitors (`awesome-cursor-rules` and similar) ship one folder you copy. v3.0 needs a shape at least that frictionless.

### 2.2 Co-active rules don't benefit from separate installs

The v2.x rule set is heavily co-active:

- Secret blocking and secrets-management apply to the same review pass.
- Cloud CLI safety, Docker safety, and supply-chain hygiene all fire on every deployment-touching change.
- Generic Python/TypeScript security applies to every code review.

Splitting them across separate installs gives users 12 chances to forget one, with no benefit because they'd want all of them anyway.

### 2.3 The Anthropic Agent Skill model rewards bundles

Skills in Anthropic's runtime are advertised to the model via `description`. The model decides per request which skills to load. With 13 narrow skills, the model performs 13 routing decisions. With one bundle, it performs one — and the body itself is structured (stable per-component subheadings) so the model navigates to relevant rules without loading the full text into working context.

Fragmentation is the right shape for **mutually exclusive** skills (e.g. "render Markdown" vs. "format Excel" vs. "draft Slack"). Security guardrails are the opposite shape: always-on, often co-active.

### 2.4 The SaaS update story stays intact

Per-component versions live inside the bundle's `catpilot.bundle.components[]` array (see `SKILL_FORMAT.md` §7). The SaaS layer can ship `secret-blocking@3.1.0` inside `catpilot-security-core@3.0.1` without forcing all components to bump. Users see one bundle version; the update layer sees 9 component versions.

Authoring granularity (per concern) ≠ install granularity (per tier). Decoupling them is what makes the SaaS story work without taxing users.

---

## 3. The 3 tiers

### Tier 1 — `catpilot-security-core` (the default install)

**One bundle skill. One install. ~90% of users stop here.**

Ships every baseline rule that fires on any code-review or codegen pass, regardless of stack. Built from these source skills under `skills/source/core/`:

| Source skill | Concern |
|---|---|
| `secret-blocking.skill.md` | Hardcoded secrets, known-format token detection, log/echo hygiene |
| `cloud-cli-safety.skill.md` | Azure / AWS / GCP / k8s / terraform destructive-command guards |
| `local-cli-safety.skill.md` | `rm -rf`, `chmod 777`, `0.0.0.0` binds, key exfiltration |
| `database-safety.skill.md` | Schema-destructive ops without confirmation, plaintext credentials |
| `docker-safety.skill.md` | Floating tags, `USER root`, `ENV SECRET=`, missing health checks |
| `secrets-management.skill.md` | Vaults, `.env` hygiene, least-privilege scopes |
| `pii-and-test-data.skill.md` | Production data in fixtures, PII in logs |
| `supply-chain.skill.md` | Pinned versions, lockfiles, `curl … | sh` from unknown sources |
| `language-baseline.skill.md` | Generic Python / TypeScript security patterns (eval/exec, deserialization) |

The two skills already authored (`secret-blocking.skill.md` and `cloud-cli-safety.skill.md`) sit in `skills/source/core/` and are starting points for the bundle. The remaining seven are tracked migration work from `copilot-instructions.md` and `FULL_GUARDRAILS.md`.

Shipped artifact: `skills/dist/catpilot-security-core.skill.md`. Body target ~20–28 KB — large but well under the ~50 KB ceiling where Anthropic Agent Skill loaders start to degrade, and well under v2.x's 32 KB monofile cap.

### Tier 2 — Framework extensions (auto-detected, opt-in)

**Additive bundles, installed automatically when the installer detects a framework. User experience: still one yes/no prompt.**

Each extension declares `catpilot.bundle.depends_on: [catpilot-security-core]` and ships small (~5–15 framework-specific rules). No content duplication with core.

| Bundle | Source location |
|---|---|
| `catpilot-django-security` | `skills/source/frameworks/django.skill.md` |
| `catpilot-fastapi-security` | `skills/source/frameworks/fastapi.skill.md` |
| `catpilot-rails-security` | `skills/source/frameworks/rails.skill.md` |
| `catpilot-express-security` | `skills/source/frameworks/express.skill.md` |
| `catpilot-nextjs-security` | `skills/source/frameworks/nextjs.skill.md` |
| `catpilot-springboot-security` | `skills/source/frameworks/springboot.skill.md` |
| `catpilot-docker-security` | `skills/source/frameworks/docker.skill.md` (compose / k8s patterns beyond core Dockerfile rules) |

Framework extensions in v3.0 are single-source-skill bundles. The bundler handles them identically to multi-source bundles; the components array just has length 1.

The installer's existing v2.x framework-detection logic (in `setup.sh`) ports cleanly to drive auto-detection.

### Tier 3 — `catpilot-security-advanced` (optional)

**For teams running agentic / multi-agent systems.**

Built from these source skills under `skills/source/advanced/`:

- `agent-identity-integrity.skill.md`
- `multi-agent-auth.skill.md`
- `cron-security.skill.md`
- `prompt-injection-tool-gating.skill.md`

Opt-in because most solo devs and traditional web-app teams don't need it. Teams building OpenClaw-style or Catpilot-style systems do.

### Net install experience

| User profile | Bundles installed | User-facing decisions |
|---|---|---|
| Solo dev, plain Python | core | 1 (yes/no) |
| Django shop | core + django | 1 (yes/no) — auto-detected |
| Next.js + Docker team | core + nextjs + docker | 1 (yes/no) — auto-detected |
| Agentic-systems team | core + framework + advanced | 1–2 |

This is the right knob. End users don't feel the source-skill decomposition; the SaaS update layer does.

---

## 4. Repo layout

```
catpilot-ai-guardrails/
├── docs/
│   └── v3-spec/
│       ├── SKILL_FORMAT.md          # file format
│       ├── PACKAGING.md             # this doc
│       ├── V2_DIAGNOSTIC.md         # adoption analysis
│       └── README.md                # index
├── skills/
│   ├── source/                      # AUTHORING granularity
│   │   ├── core/                    # → bundles into catpilot-security-core
│   │   │   ├── secret-blocking.skill.md         ✓ done
│   │   │   ├── cloud-cli-safety.skill.md        ✓ done
│   │   │   ├── local-cli-safety.skill.md        (migration)
│   │   │   ├── database-safety.skill.md         (migration)
│   │   │   ├── docker-safety.skill.md           (migration)
│   │   │   ├── secrets-management.skill.md      (migration)
│   │   │   ├── pii-and-test-data.skill.md       (migration)
│   │   │   ├── supply-chain.skill.md            (migration)
│   │   │   └── language-baseline.skill.md       (migration)
│   │   ├── frameworks/              # → one bundle per framework
│   │   │   └── (migration from frameworks/*/condensed.md)
│   │   └── advanced/                # → bundles into catpilot-security-advanced
│   │       └── (migration)
│   └── dist/                        # SHIPPING granularity (generated)
│       ├── catpilot-security-core.skill.md
│       ├── catpilot-django-security.skill.md
│       └── catpilot-security-advanced.skill.md
└── (existing v2.x files on main: copilot-instructions.md, setup.sh, frameworks/, etc.)
```

The two existing source skills are real — production-grade content authored against the spec. The (migration) entries are tracked work that follows once this packaging strategy is approved.

---

## 5. The bundler

A small, deterministic build script. Inputs: `skills/source/<tier>/...`. Outputs: `skills/dist/*.skill.md`.

**Determinism requirements:**

1. Stable component order (taken from a `bundle-manifests/<tier>.yaml` config or sorted alphabetically — TBD, low-stakes).
2. Stable `### <component-id>` heading slugs in the body.
3. No timestamps, no build-host info, no random IDs in the output.
4. Two builds from the same source tree produce byte-identical bundle files.

**Aggregation logic** (per `SKILL_FORMAT.md` §7.3):

- Bundle `severity` = max(component.severity).
- Bundle `control_mappings.<framework>` = sorted union(component values).
- Bundle `applies_to.languages` / `.frameworks` = intersection if all components specify, else `[any]`.
- Per-component `version` recorded in `catpilot.bundle.components[]`.

**Implementation:** ~150 lines of Python or Go. Runs in CI on every PR; bundles are committed (so end users cloning `dist/` get them without running the bundler) and CI verifies they match what the bundler would produce.

This doc doesn't prescribe the language. The bundler is small and replaceable; what matters is the determinism contract.

---

## 6. Distribution

Recommendation, not commitment. Tracked as an open question in `README.md`'s decision log.

**Primary: npm.** `npx @catpilot/ai-guardrails install`. One command, auto-detects framework, installs the right tier mix per detected runtime (`~/.claude/skills/`, `.cursor/rules/`, `~/.openclaw/skills/`, etc.).

**Alternatives:**
- **pip** — fast-follow for Python-only shops post-v3.0.
- **brew** — later, macOS-only.
- **Legacy submodule + `setup.sh`** — stays available through v3.x for existing users; README points new users at npm.

The packaging strategy in this doc is **distribution-agnostic**. Whatever wrapper we ship (`npx`, `pip install`, `brew install`, manual clone) the user-facing experience is the same: install one bundle per tier, auto-detect framework extensions.

---

## 7. Bundle vs source — quick reference for contributors

| You are… | Touch this | Don't touch this |
|---|---|---|
| Adding a new rule | A source skill in `skills/source/<tier>/...` | `skills/dist/...` (regenerated by bundler) |
| Adding a framework | A new `skills/source/frameworks/<framework>.skill.md` | The bundler config (it picks up new files automatically) |
| Promoting an experimental rule to GA | Bump source skill version, the bundler picks up the change on next CI run | The bundle frontmatter (the bundler computes it) |
| Reading what end users see | A `skills/dist/*.skill.md` bundle | A source skill (it's a build input) |

If a contributor is editing `skills/dist/*.skill.md` directly, the PR is wrong; they want a source file.

---

## 8. Open questions

1. **Tier 3 naming — `catpilot-security-advanced` or `catpilot-security-agentic`?** "Agentic" is more descriptive but the term is overloaded across the market. Leaning `advanced`.
2. **Compliance mapping default set.** Spec defaults to NIST CSF, SOC2, ISO 27001, PCI DSS, OWASP Top 10. Add HIPAA / GDPR for v3.0, or keep tight and grow later? Keeping tight reduces validator surface.
3. **Distribution path lock-in.** Pull `npx` from "recommended" to LOCKED in the decision log now, or defer to v3.0 launch? The packaging strategy is robust to either.
4. **Bundler language.** Python (lower deps for contributors, matches Catpilot platform) or Go (single static binary, no install)? Low-stakes; can be revisited.

---

## 9. Decisions made in this doc (assuming approval)

| # | Decision | Rationale |
|---|---|---|
| A | Authoring unit = source skill (per concern); install unit = bundle (per tier) | Decouples SaaS update granularity from user install friction |
| B | 3 tiers: core / framework extensions / advanced | Matches user profiles; all but advanced auto-installed |
| C | Source skills live under `skills/source/<tier>/...` | Disjoint from `skills/dist/` so the unit of authorship is unambiguous |
| D | Bundles live under `skills/dist/...`, generated by the bundler, committed | Reproducible, no install-time build, end users get bundles directly from clones |
| E | Bundle frontmatter records per-component versions in `catpilot.bundle.components[]` | Preserves SaaS update story without leaking it to end-user UX |
| F | Bundler aggregates severity (max), control mappings (union), applies-to (intersection or `any`) | Mechanical; no hand-edited bundle metadata |

When approved, these flip to LOCKED in the v3-spec README decision log.
