---
name: Cloud CLI Safety
description: |
  Require query-before-modify, full-command display, explicit confirmation,
  and rollback preparation before any cloud CLI invocation that mutates
  infrastructure. Covers Azure (`az`), AWS (`aws`), GCP (`gcloud`, `gsutil`),
  Kubernetes (`kubectl`, `helm`), and Terraform/IaC (`terraform`). Born from
  a real production incident where a partial-YAML container update wiped
  every environment variable on a live service.
catpilot:
  id: cloud-cli-safety
  version: 1.0.0
  severity: critical
  category: cloud-cli
  applies_to:
    languages: [any]
    frameworks: [any]
    runtimes: [claude-code, cursor, openclaw, cline, aider, copilot, codex-cli]
  control_mappings:
    soc2: [CC6.1, CC7.2, CC8.1, A1.2]
    pci_dss: ["6.4.5", "6.4.5.2", "10.2"]
    iso_27001: [A.12.1.2, A.12.5.1, A.14.2.2, A.14.2.3]
    nist_csf: [PR.IP-1, PR.IP-3, DE.CM-7, RS.MI-2]
    owasp_top_10: [A05:2021, A08:2021]
  provenance:
    origin: catpilot
    incident_derived: true
  references:
    - https://learn.microsoft.com/en-us/azure/container-apps/azure-resource-manager-api-spec
    - https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-best-practices.html
    - https://cloud.google.com/sdk/docs/best-practices
    - https://kubernetes.io/docs/concepts/overview/working-with-objects/object-management/
  maintainers:
    - team: catpilot-security
---

## Why

This skill exists because of a specific outage.

An AI assistant was asked to update the liveness probe on an Azure Container
App. It generated a small YAML file containing only the `probes:` block and
ran:

```bash
az containerapp update --yaml probes-only.yaml
```

The Azure Resource Manager API treats `--yaml` as a **full-resource
replacement**, not a patch. Every field absent from the file was reset to
its default. Within seconds:

- CPU dropped from 2.0 cores to 0.5 (default) — 75% capacity loss.
- Memory dropped from 4 GiB to 1 GiB — 75% loss.
- **Every environment variable was deleted**, including database
  connection strings and third-party API keys.
- Liveness probes started failing because the app could no longer reach the
  database.
- The service was effectively down until env vars were restored from a
  separate vault and the container was re-provisioned.

The agent did exactly what it was told. The CLI did exactly what it was
documented to do. The failure was at the seam: the agent did not query the
existing state, did not show the operator the full blast radius, and did
not prepare a rollback before pressing enter.

This is not an Azure-specific failure mode. The same shape exists in:

- `aws lambda update-function-configuration --environment "Variables={ONLY_ONE=value}"` — replaces, does not merge.
- `gcloud projects set-iam-policy PROJECT policy.json` — overwrites all IAM bindings.
- `gcloud run services update SERVICE --set-env-vars ONLY_ONE=value` — clears the rest.
- `kubectl apply -f partial.yaml` against a resource managed elsewhere — race condition + field reset.
- `terraform apply` against drifted state — destroys whatever the state file no longer remembers.

The rule is the same on every cloud: **query → display → confirm → execute → verify → keep rollback ready.**

## When to apply

Apply whenever the agent is about to invoke any of:

- `az` (any subcommand that is not pure read: `show`, `list`, `get-*`)
- `aws` (any subcommand starting with `create`, `update`, `delete`, `put`, `start`, `stop`, `terminate`, `attach`, `detach`, `set-`)
- `gcloud` / `gsutil` (any subcommand that is not pure read)
- `kubectl` (`apply`, `create`, `delete`, `patch`, `replace`, `scale`, `rollout`, `cordon`, `drain`, `taint`)
- `helm` (`install`, `upgrade`, `uninstall`, `rollback`)
- `terraform` (`apply`, `destroy`, `import`, `state mv`, `state rm`, `taint`)
- Any custom wrapper script (`./deploy.sh`, `make deploy`) where the body is unknown to the agent

Apply with **maximum severity** when the target matches production
heuristics: hostnames or resource names containing `prod`, `production`,
`live`, `prd`; env vars `NODE_ENV=production` or `ENV=prod`; git branch
`main`, `master`, `production`, or `release/*`.

## Rules

### Universal six-step protocol

> [!agent] Before executing any mutating cloud CLI command, complete all
> six steps in order. Do not skip step 4 even if the user has previously
> said "go ahead" in this session — confirmation is per-command.

1. **[critical]** **Query current state.** Run the read-only equivalent
   first and show the relevant fields to the user.
2. **[critical]** **Show the full command.** No truncation, no `…`, no
   variable interpolation hidden behind `$VAR`. Expand everything.
3. **[critical]** **Enumerate fields that will change.** Especially env
   vars, IAM bindings, replica counts, CPU/memory, probes.
4. **[critical]** **Get explicit confirmation.** A literal "yes" or
   equivalent. Do not infer consent.
5. **[high]** **Prepare a rollback.** Write the rollback command to a
   scratch file or print it before executing the forward command.
6. **[high]** **Verify after execution.** Re-run the read-only query and
   diff against the pre-change snapshot.

### Always-blocked patterns

- **[critical]** `az containerapp update --yaml <partial>` — overwrites all unspecified fields.
- **[critical]** `az containerapp update --set-env-vars X=Y` without first reading existing env — clears every other env var.
- **[critical]** `aws lambda update-function-configuration --environment "Variables={ONLY_ONE=value}"` — replaces, does not merge.
- **[critical]** `aws s3 rm s3://bucket --recursive` without prior `aws s3 ls` and explicit confirmation.
- **[critical]** `gcloud projects set-iam-policy PROJECT policy.json` — wipes existing bindings. Use `add-iam-policy-binding` instead.
- **[critical]** `gcloud run services update SERVICE --set-env-vars X=Y` without reading existing env vars.
- **[critical]** `gcloud app versions delete --all --quiet`.
- **[critical]** `gcloud run services delete SERVICE --quiet`.
- **[critical]** `gsutil rm -r gs://bucket/**` without inventory.
- **[critical]** `terraform apply -auto-approve`, `terraform destroy -auto-approve`. Auto-approve is banned anywhere production is plausible.
- **[critical]** `kubectl delete namespace production` (or anything matching production heuristics).
- **[critical]** `kubectl delete pods --all -n <ns>` against a non-dev namespace.
- **[critical]** `kubectl apply -f -` reading from stdin without showing the manifest first.
- **[high]** `helm upgrade RELEASE CHART` without prior `helm diff upgrade` (requires the helm-diff plugin).
- **[high]** Any `--force` flag on `kubectl delete`.
- **[high]** Any `--quiet` / `-q` / `--yes` / `-y` flag on a mutating command. The agent must not use these.

### Always-required patterns

- **[high]** Use **additive** IAM commands (`add-iam-policy-binding`) over **replace** commands (`set-iam-policy`).
- **[high]** Use `--dry-run=client` (kubectl) or `terraform plan -out=tfplan` (then `terraform apply tfplan`) before any apply.
- **[high]** When updating env vars, **read all current env vars first** and pass the full merged set on the update command.
- **[medium]** Pin Terraform provider versions; never use `latest`.
- **[medium]** For multi-resource changes, prefer one mutating command per turn so each can be confirmed individually.

## Negative examples

```bash
# ❌ Azure: partial YAML wipes everything not in the file
az containerapp update \
  --name myapp --resource-group prod-rg \
  --yaml probes-only.yaml
```

```bash
# ❌ AWS Lambda: replaces the entire environment block
aws lambda update-function-configuration \
  --function-name api-prod \
  --environment "Variables={NEW_FLAG=true}"
```

```bash
# ❌ GCP: replaces all IAM bindings on the project with whatever is in policy.json
gcloud projects set-iam-policy my-project policy.json
```

```bash
# ❌ Kubernetes: nukes a production namespace, no confirmation
kubectl delete namespace production
```

```hcl
# ❌ Terraform: auto-approve in a script that runs in CI against prod state
terraform apply -auto-approve
```

```bash
# ❌ S3: recursive delete without listing
aws s3 rm s3://customer-backups --recursive
```

```bash
# ❌ Helm: upgrade with no diff, no values inspection
helm upgrade prod-api ./chart
```

## Remediation

### Azure Container Apps — preserve env vars on update

```bash
# ✅ Step 1: Query
az containerapp show \
  --name myapp --resource-group prod-rg \
  --query "properties.template.containers[0].env" -o json > current-env.json

# ✅ Step 2: Patch only the field you want, keep the rest
jq '. + [{"name":"NEW_FLAG","value":"true"}]' current-env.json > merged-env.json

# ✅ Step 3: Show full command, get confirmation, then update
az containerapp update \
  --name myapp --resource-group prod-rg \
  --set-env-vars $(jq -r '.[] | "\(.name)=\(.value)"' merged-env.json | tr '\n' ' ')

# ✅ Rollback prepared in advance
echo "az containerapp update --name myapp --resource-group prod-rg \\
  --set-env-vars $(jq -r '.[] | \"\\(.name)=\\(.value)\"' current-env.json | tr '\n' ' ')" \
  > rollback.sh
```

### AWS Lambda — merge env vars instead of replace

```bash
# ✅ Read existing
aws lambda get-function-configuration --function-name api-prod \
  --query 'Environment.Variables' --output json > current.json

# ✅ Merge
jq '. + {"NEW_FLAG":"true"}' current.json > merged.json

# ✅ Update with the FULL merged set
aws lambda update-function-configuration \
  --function-name api-prod \
  --environment "Variables=$(jq -c . merged.json)"
```

### AWS S3 — list before recursive delete

```bash
# ✅ Inventory first
aws s3 ls s3://customer-backups --recursive --summarize | tee s3-inventory.txt

# ✅ Confirm count, then prepare rollback (versioning must be on; otherwise refuse)
aws s3api get-bucket-versioning --bucket customer-backups
# Only proceed if "Status": "Enabled"

# ✅ Then delete, with --dryrun first
aws s3 rm s3://customer-backups --recursive --dryrun
# Review output, get confirmation, drop --dryrun
aws s3 rm s3://customer-backups --recursive
```

### GCP IAM — additive, not replace

```bash
# ✅ Add a single binding without touching the rest
gcloud projects add-iam-policy-binding my-project \
  --member="user:alice@example.com" \
  --role="roles/viewer"

# ✅ Remove a single binding
gcloud projects remove-iam-policy-binding my-project \
  --member="user:bob@example.com" \
  --role="roles/editor"

# ✅ Snapshot policy before any structural change
gcloud projects get-iam-policy my-project --format=json > iam-backup.json
```

### GCP Cloud Run — preserve env vars

```bash
# ✅ Read existing env
gcloud run services describe my-service --region us-central1 \
  --format='value(spec.template.spec.containers[0].env)' > current-env.txt

# ✅ Use --update-env-vars (merge) — NOT --set-env-vars (replace)
gcloud run services update my-service --region us-central1 \
  --update-env-vars NEW_FLAG=true
```

### Kubernetes — dry-run, diff, then apply

```bash
# ✅ Dry-run (server-side preferred — catches admission webhook errors)
kubectl apply -f deploy.yaml --dry-run=server

# ✅ Diff against live state
kubectl diff -f deploy.yaml

# ✅ Apply only after reviewing diff
kubectl apply -f deploy.yaml

# ✅ Rollout history kept; rollback ready
kubectl rollout history deployment/api -n production
# Rollback: kubectl rollout undo deployment/api -n production
```

### Helm — diff plugin required for upgrades

```bash
# ✅ Install the diff plugin once
helm plugin install https://github.com/databus23/helm-diff

# ✅ Diff before upgrade
helm diff upgrade prod-api ./chart -f values.prod.yaml

# ✅ Upgrade only after reviewing diff
helm upgrade prod-api ./chart -f values.prod.yaml --atomic --timeout 5m

# ✅ Rollback ready
helm history prod-api
# Rollback: helm rollback prod-api <REVISION>
```

### Terraform — plan files, never auto-approve

```bash
# ✅ Always use a saved plan
terraform plan -out=tfplan
# Review plan output for unexpected destroys/replaces, especially:
#   - resources marked "must be replaced"
#   - any "destroy" not explicitly intended

# ✅ Apply the exact plan that was reviewed
terraform apply tfplan

# ✅ State changes — separate from apply, also reviewed
terraform state list
terraform state show <addr>

# ❌ Never in any environment that could be production
# terraform apply -auto-approve
# terraform destroy -auto-approve
```

### Rollback templates by platform

| Platform | Rollback |
|---|---|
| Azure Container Apps | `az containerapp revision activate --revision <prev-rev>` |
| AWS Lambda | `aws lambda update-function-configuration --function-name X --environment file://rollback-env.json` |
| Cloud Run | `gcloud run services update-traffic SERVICE --to-revisions=PREV=100` |
| App Engine | `gcloud app services set-traffic default --splits=PREVIOUS_VERSION=1` |
| Kubernetes | `kubectl rollout undo deployment/X -n NS` |
| Helm | `helm rollback RELEASE <REVISION>` |
| Terraform | Restore prior state file from versioned backend (S3 versioning, GCS, Terraform Cloud) and `terraform apply` again |

## Production detection heuristics

Treat **any** of the following as production until proven otherwise:

- Resource name, hostname, or namespace contains: `prod`, `production`, `live`, `prd`.
- Env var: `NODE_ENV=production`, `ENV=prod`, `ENVIRONMENT=production`, `APP_ENV=prod`.
- Current git branch matches: `main`, `master`, `production`, `release/*`.
- Cloud subscription / project / account name contains the above tokens.
- DNS name resolves to a public IP that responds with a non-staging cert SAN.

When production is detected, **escalate confirmation**: require the user
to type the resource name back, not just "yes". This is consistent with
how AWS, GCP, and Azure consoles handle destructive console actions.

## References

- Azure Container Apps update semantics: <https://learn.microsoft.com/en-us/azure/container-apps/azure-resource-manager-api-spec>
- AWS CLI best practices: <https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-best-practices.html>
- GCP CLI best practices: <https://cloud.google.com/sdk/docs/best-practices>
- Kubernetes object management: <https://kubernetes.io/docs/concepts/overview/working-with-objects/object-management/>
- helm-diff plugin: <https://github.com/databus23/helm-diff>
- Terraform plan/apply workflow: <https://developer.hashicorp.com/terraform/cli/run>
