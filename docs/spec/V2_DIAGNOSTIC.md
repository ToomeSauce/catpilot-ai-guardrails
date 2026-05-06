# v2.x Diagnostic — Why Zero External Stars

**Status:** Internal candid memo
**Author:** Catpilot security
**Audience:** Catpilot team, relaunch planning
**Framing:** This is not blame. This is data. v2.1.0 has 0 external stars
and 0 forks at time of writing. We need to understand why before we
spend more product work on the same shape and expect a different result.

---

## TL;DR

v2.x is a solid piece of *content* sitting behind two separable problems:

1. **Distribution problem (most likely root cause).** No identifiable
   launch motion. The repo exists; nobody who would star it knows it
   exists. Zero stars is consistent with "product was never seen by the
   target audience," not necessarily with "product was seen and rejected."
2. **Packaging problem (secondary).** Even if a security engineer found
   the repo, the install path is unusual (git submodule + bash setup
   script that writes to `.github/`), the artifact (a single
   `copilot-instructions.md`) doesn't map to how the broader skills
   ecosystem is converging (Anthropic Agent Skills, Cursor rules, etc.),
   and the README leads with the install command rather than the
   problem-and-proof.

The rewrite's bet — recast the content as Anthropic-Agent-Skill-compatible
`.skill.md` files — addresses the packaging problem. It does **not** by
itself address the distribution problem. Both need a deliberate plan.

What we do not know, and should be honest about: we have no analytics
showing how many people clicked through, cloned, ran setup, and bounced
versus how many never saw the repo at all. We have no qualitative
feedback from a target user who tried v2.x and chose not to use it. The
diagnostic below is an inference exercise, not a measurement.

---

## 1. README clarity audit

The current README opens with:

> Most coding agents read a local file for project-specific guidance—but
> most teams leave it empty. Drop in these guardrails to catch dangerous
> patterns that cause **outages, security vulnerabilities, and secret
> leaks.**

Then immediately moves to a Quick Start with three `git submodule`
commands.

### What works

- The "born from a real incident" framing is good. It's specific and
  credible. (We should keep this in the rewrite.)
- The Tool Support table is concrete. A reader scanning for "does this
  work with my setup" gets an answer in five seconds.
- "What It Catches" is a good visual scan target.

### What doesn't

- **Lede buries the proof.** A skeptical security engineer's first
  question is "is this any good?", not "how do I install it?". The
  install block appears before any example of caught behavior. The
  example of cloud-CLI protection is hundreds of lines down, after the
  Tool Support table.
- **No "vs alternatives" anchor.** The reader cannot quickly tell
  whether this is a competitor to Snyk, Semgrep, GitGuardian, Cursor's
  built-in rules, or something different. A 1-line positioning
  statement ("agent-time guardrails, not CI-time scanning") would help.
- **No social proof.** No logos, no quotes, no usage count. For a
  security tool from an unknown brand, this is a high friction barrier.
  We can't manufacture this, but we can at least show our own
  dogfooding metrics ("Catpilot uses these in N internal repos").
- **The framework table is impressive but premature.** The reader sees
  "11 frameworks supported" before they understand what a framework
  rule looks like. Move it down.
- **No screenshot or terminal recording.** Security tools live or die
  on whether you can picture using them. There is no asciicast, no GIF,
  no example of an agent refusing a dangerous command.

### Recommendation for the new README

Restructure the README in this order:

1. **Logo + tagline** (one line — keep "Paws before you push.").
2. **One-paragraph positioning** with the alternative-anchor: "X is
   skills, not scans. They run inside your coding agent, before the
   command executes — not in CI after the fact."
3. **One concrete example, terminal-recorded.** The partial-YAML wipe
   story, captured as an asciicast: agent generates dangerous command,
   skill blocks it, shows the safe alternative. ~20 seconds.
4. **Install (3 lines).**
5. **What it catches** (the icon list, kept short).
6. Everything else (frameworks, organizations, codex CLI) goes into
   collapsed `<details>` blocks.

---

## 2. Install-friction audit

Current install:

```bash
git submodule add https://github.com/catpilotai/catpilot-ai-guardrails.git \
  .github/catpilot-ai-guardrails
./.github/catpilot-ai-guardrails/setup.sh
git add .gitmodules .github/
git commit -m "Add AI guardrails"
```

### Friction points

- **Submodules are unpopular.** Most teams who have used submodules have
  a story about getting burned by them. Asking a security-conscious
  engineer to add a submodule to *every repo they own* is asking a lot.
  The submodule also implies a transitive trust relationship with our
  GitHub org — a real concern for anyone who has watched the npm or
  PyPI supply-chain incidents of the last three years.
- **Bash installer.** A 424-line bash script that writes into
  `.github/` (and other locations) is a non-trivial trust ask. A
  skeptical engineer reads it before running it. Some of them will
  bounce at "424 lines" alone. The script does sensible things, but the
  reader has to verify that.
- **Hidden symlinks.** The script creates symlinks to `.cursorrules`,
  `CLAUDE.md`, `.clinerules`, etc. This means the artifact a reviewer
  sees in their repo is a symlink to a file inside `.github/`. Reviewers
  who have not read the README will be confused.
- **`.github/catpilot-ai-guardrails/` is not a path teams use.** Most
  `.github/` content is GitHub-specific (workflows, issue templates).
  Putting agent rules there pattern-matches to "this is GitHub
  Actions-related," which it isn't.
- **No package-manager path.** No `npm install`, `pip install`, `brew
  install`, no `gh ext install`. Every modern dev tool that wins
  distribution offers at least one of these.

### Recommendation for the rewrite

- Move the canonical install away from submodules. Options:
  - **`npx catpilot-skills install`** — copies/symlinks the chosen
    skills into the right per-runtime directory. No persistent
    submodule. `npx` works without a global install.
  - **`gh ext install catpilot/skills`** — for GitHub-native users.
  - **Manual copy.** A single command that downloads a tarball and
    unpacks into `skills/`. Lowest-trust install path, important for
    paranoid users.
- Keep the submodule path as a documented option for orgs that want
  pinned, audited, fork-controlled versions. Don't lead with it.
- Move skills out of `.github/`. Use `skills/` (or `.claude/skills/` /
  `.cursor/rules/` per runtime). The `.github/` location made sense
  when the only target was Copilot's `copilot-instructions.md`. the rewrite's
  per-skill-file model doesn't need it.
- Ship a 3-line `<details>` "is this safe to install?" section in the
  README that links to the audit-friendly file layout: each skill is a
  single Markdown file under 500 lines, no executables, no network
  calls. Low review cost is itself a feature.

---

## 3. Distribution effort audit

This is the section where we have to be honest about what we don't
know. The repo exists. v2.0.0 shipped 2026-02-06; v2.1.0 shipped
2026-03-06. As of the date of this memo:

- **Stars:** 0 external (per the brief).
- **Forks:** 0 external.
- **Open issues / PRs from outside contributors:** unknown to me;
  recommend pulling the count before the launch retro.
- **HN / Lobsters / Reddit submission count:** unknown, recommend
  searching `hn.algolia.com` and Reddit for the repo URL.
- **Mentions in the security newsletters (tldrsec, Hacker Newsletter,
  Risky Biz):** unknown, recommend searching their archives.
- **Conference / podcast mentions:** unknown.

The honest framing: **we do not know whether v2.x was tried and rejected,
or simply never seen.** The shape of zero stars (not "low stars, slow
growth") is more consistent with "never seen by the target audience"
than "seen and bounced," because even a bad security tool with a real
release tends to attract a handful of curious stars from the security
Twitter / Mastodon / Bluesky ecosystem.

### What we should check before the relaunch

- GitHub Insights → Traffic → past 14 days. Clones, unique visitors,
  referrers. Even a few referrers tell us whether anyone shared the
  link.
- Search `site:news.ycombinator.com catpilot-ai-guardrails`,
  `site:reddit.com catpilot-ai-guardrails`, `site:lobste.rs`.
- `npm` and `pypi` for typosquats / similar names — if the namespace is
  contested, that affects the new packaging.

### What an actual relaunch looks like

If we're treating v2.x as a "soft beta that nobody noticed" and the rewrite as
the real launch, the launch motion needs to exist. Recommend:

- **One launch artifact.** A blog post on a domain that actually has
  some inbound (`catpilot.ai/blog/...`) telling the partial-YAML
  incident story end-to-end, with the `.skill.md` worked examples
  inline. The post is the canonical thing we point everywhere else at.
- **Three distribution channels, in order of likely yield.**
  1. **HN Show**. Title format: "Show HN: Catpilot — open-source
     security skills for coding agents (Anthropic-Skill-compatible)".
     The Anthropic-Skill compatibility is the hook; "another security
     tool" is not.
  2. **r/devops, r/cybersecurity, r/programming**. Same post, adapted.
  3. **Targeted DMs / replies** in the AI-coding community: people
     posting about Cursor, Claude Code, OpenClaw, agent setups. Don't
     spam; one substantive reply per relevant thread.
- **Two follow-on artifacts within 30 days.** A second blog post on a
  specific skill (e.g., a deep dive on the cloud-CLI patterns and the
  real-world incident), and a short video / asciicast walkthrough.
- **Cross-post the launch in the Anthropic Skills / Claude Code
  communities** if those have organized presence. The compatibility
  story is the right wedge there.

### What we should not do

- **Buy stars.** Obvious, but stating it. Zero stars from real users is
  better than 200 stars from bots, both ethically and because anyone
  evaluating the repo will check the star pattern.
- **Astroturf.** Same reasoning.
- **Soft-launch without telling anyone.** v2.x already did that; the
  outcome is the data point we're working from.

---

## 4. Positioning / SEO audit

### Where we sit

Searching for the obvious queries (anonymized speculation, validate
before launch):

- "AI coding agent guardrails" — likely returns Cursor, Claude, Copilot
  vendor pages, not third-party tooling.
- "secret detection coding agent" — likely returns GitGuardian,
  TruffleHog, GitHub secret scanning.
- "Cursor security rules" — sparse, this is a real opportunity.
- "Anthropic Agent Skills security" — very sparse, likely a real
  opportunity for the rewrite if we lead with skill-format compatibility.

### Recommendations

- **Lead positioning with "skills" not "guardrails."** "Guardrails" is
  a saturated term (LangChain Guardrails, NVIDIA NeMo Guardrails, etc.)
  and points the reader toward LLM-output-shaping tools, which is not
  what this is. "Security skills for coding agents" is more specific
  and competes in a thinner field.
- **Make the Anthropic Skills compatibility a top-of-fold claim.**
  This is the actual differentiator in the rewrite. If a reader's mental model
  is "I already know what an Agent Skill is," the install becomes
  "drop these files in your skills directory" — much lower trust ask.
- **Own a few specific search phrases** with content:
  - "Anthropic Agent Skill security examples" → SKILL_FORMAT.md +
    worked examples.
  - "Cursor security rules secret detection" → a skill-specific page.
  - "agent-time SQL injection prevention" → another.
- **Title and OG metadata on the GitHub repo.** Small but real:
  `description` on the repo, topics (`security`, `ai-agents`,
  `claude-code`, `cursor`, `anthropic-skills`, `secret-detection`).
- **The README's H1 should match a query.** Right now it's "Guardrails
  for Coding Agents." Consider "Security Skills for Coding Agents"
  for the rewrite.

---

## 5. Concrete recommendations for the relaunch motion

In priority order. (The product changes — `.skill.md`, format spec,
worked examples — are tracked in `docs/spec/SKILL_FORMAT.md` and the
`skills/*.skill.md` files.)

### Must-have before launch

1. **Restructure README.** Lead with one terminal-recorded example, then
   install. Move framework details into `<details>`.
2. **Replace submodule install with `npx catpilot-skills install` (or
   equivalent).** Keep submodule as a secondary documented path.
3. **Move skills out of `.github/` to `skills/`.**
4. **One launch blog post on `catpilot.ai`** with the partial-YAML
   incident as the lead anecdote and the worked examples inline.
5. **Repo metadata.** Topics, description, social preview image.

### Should-have

6. **Asciicast or 30-second video** showing an agent being blocked by a
   skill. Embed in README and blog post.
7. **Show HN submission** with a thoughtful title and a top-comment
   plan (a comment from us that frames the post and offers to answer
   questions in-thread).
8. **r/devops / r/programming cross-posts.**
9. **Compatibility table on the repo:** "Skill format: Anthropic Agent
   Skill superset. Works in Claude Code, Cursor, OpenClaw, Cline,
   Aider, Copilot. Same file, every runtime."

### Nice-to-have

10. **Write up the spec in a separate post for security-engineer
    audiences** (positioning: "we wrote down what a security skill
    file should look like; here's the spec").
11. **Submit to one or two security newsletters** (tldrsec, Risky Biz)
    once we have a week of post-launch telemetry to point at.
12. **Pin a "good first contribution" issue** for new skills — invites
    community without requiring it.

---

## 6. What we don't know — instrument before launch

To make v3.x launch decisions better than v2.x's, we need data v2.x
didn't collect. Without violating the OSS = zero phone-home rule, we
can still get:

- **GitHub Insights → Traffic** (clones, unique visitors, referrers).
- **GitHub stars over time** as the most basic interest signal.
- **`gh api` queries** for fork count, issue and PR origin (internal vs
  external).
- **Public mentions search** (HN, Reddit, Mastodon, Bluesky, Lobsters)
  weekly for the first 4 weeks post-launch.
- **`catpilot.ai/blog/...`** standard web analytics on the launch post
  (this lives on our site, not in the OSS repo, so zero-phone-home
  doesn't apply).

If we want anything beyond that — e.g., "did the user complete install
successfully?" — that's a SaaS feature, not an OSS one. Out of scope
here per architectural commitment.

---

## 7. The honest bottom line

The v2.x content is good. The v2.x distribution effort, as far as we
can tell, did not happen at meaningful scale. the rewrite's format work is
necessary but not sufficient. If we ship the rewrite with the same launch
motion as v2.x — push to GitHub, hope — we will get the same result.

The work plan should be 60% packaging (which is already mostly drafted
in this PR), 40% launch. Right now we are weighted ~95/5.
