# tools/

Build and validation scripts for the v3.0 skill format.

## bundle.py

Deterministic bundler that reads source skills under `src/skills/<tier>/<name>/SKILL.md` and produces shipped bundles at `skills/<bundle-name>/SKILL.md` in the [Anthropic Agent Skills](https://agentskills.io/specification) format that [`npx skills add`](https://github.com/vercel-labs/skills) installs.

```bash
# build all tiers
python tools/bundle.py

# build a single tier (matches src/skills/<tier> directory name)
python tools/bundle.py --tier core

# CI mode: fail if skills/ isn't the deterministic output of src/skills/
python tools/bundle.py --check
```

Determinism contract is in [`docs/v3-spec/PACKAGING.md` §5](../docs/v3-spec/PACKAGING.md). Aggregation rules (severity = max, control_mappings = sorted union, applies_to = union with `any` collapse, components in lexicographic order by id) are in §3.2.

The bundler runs on every PR via `.github/workflows/bundle-check.yml`. If you edit a source skill and forget to rebuild, the check fails with a unified diff pointing at the drift.

### Dependencies

- Python 3.11+ (uses `tomllib` from the stdlib).
- `pyyaml` for frontmatter parsing.
