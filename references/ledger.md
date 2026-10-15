# Optional local ledger helper

Requires Python 3.10 or later and its standard library. No packages, network,
browser or credentials are needed. Run commands from the skill folder or use
the script's absolute path. Evidence belongs in the audit workspace, not here.

## Initialize and define coverage

```bash
python3 scripts/audit_ledger.py init --out /tmp/my-project-audit --project "Example CLI" --type cli
```

This creates an unassessed `audit.json`, `evidence/` and `reports/`. It does not
execute tests. Populate `scope.coverage`, `scope.exclusions` and the test cases
after inspecting the actual project. Do not use an empty ledger to claim readiness.

Example case object in `cases`:

```json
{
  "id": "T01",
  "area": "security",
  "objective": "Reject output paths outside the selected workspace",
  "actor": "Local CLI user",
  "environment": "Isolated temporary workspace",
  "expected": "Reject the path and leave the external target untouched",
  "required": true,
  "critical": true,
  "runs": []
}
```

Areas are `security`, `delivery` or `shared`. A shared case appears in both reports;
do not sum those reports' counts as if the cases were different tests. `required`
identifies the agreed acceptance scope; `critical` also makes a case required for
the ready assessment. Human judgment still determines whether that scope is enough.

## Append attempts and freeze their evidence hashes

Capture a sanitized actual command/test log under `evidence/`. Use distinct paths
per attempt. Then prepare an event file, for example `/tmp/my-run.json`:

```json
{
  "status": "failed",
  "version": "baseline-commit-or-build-id",
  "observed": "The CLI accepted the path and wrote outside its workspace",
  "command": "The exact reproducible command with secrets removed",
  "exit_code": 0,
  "evidence": [{"path": "evidence/T01-before.txt"}]
}
```

The observation here is only a format example; do not record it unless witnessed.
An exit code of zero can still represent a failed functional/security expectation.
The `status` expresses the expected contract, not just process success.

```bash
python3 scripts/audit_ledger.py record /tmp/my-project-audit/audit.json --case T01 --run /tmp/my-run.json
```

The helper adds a UTC timestamp if absent and SHA-256 hashes of the referenced
files. After correction, record a separate passing event and evidence file on the
fixed version. Previous attempts remain. `check` rejects changed/missing hashed
evidence. New evidence invalidates an existing readiness declaration until the
auditor reassesses it; a failed retest reopens findings tied to that retest.

Valid statuses: `passed`, `failed`, `blocked`, `not_tested`, `not_applicable`.
Executed passes/failures require evidence. The last three require a `reason`.
Use an ISO timestamp with timezone when specifying `at` explicitly. Do not place
secrets in `command`, observations, filenames, images or any other ledger field.

File references are relative to the ledger directory. Absolute paths, `..` and
symlinks outside it are rejected. External evidence such as CI status should be
saved as a sanitized local record with the source URL inside it. Files are never
executed by the helper.

## Findings and screenshots

Example finding object, to adapt to actual evidence:

```json
{
  "id": "F01",
  "area": "security",
  "title": "Output escapes the workspace",
  "origin": "reproduction",
  "severity": "high",
  "impact": "An operator could overwrite files outside the chosen output directory",
  "status": "corrected",
  "evidence": [{"path": "evidence/T01-before.txt"}],
  "correction": "Describe the implemented root-cause fix and its change reference",
  "retest_ids": ["T01"],
  "residual_risk": "Describe actual limits of this verification"
}
```

Severities: `critical`, `high`, `medium`, `low`, `info`. Statuses: `open`,
`corrected`, `not_reproduced`, `excluded`. Corrected findings need a correction and
passing retest IDs; excluded/not-reproduced dispositions need a `reason`. Do not
use exclusion to hide an observed failure. Before evidence may come from a safe
inspection instead of an exploit; record the actual `origin`.

Screenshots use `path`, `caption`, `area`, optional `sha256`, and
`reviewed_for_secrets: true`. Set the last field only after inspecting the image.
The script cannot detect passwords in screenshot pixels. No screenshot is required
for a project without a relevant UI; use actual logs and artifacts instead.

## Assessment, delivery and sources

`assessment.status` accepts `not_assessed`, `not_ready`, `conditional` or
`ready_within_scope`. All conclusions except not-assessed need a rationale;
conditional also needs conditions. An unresolved critical finding or failed
critical case requires not-ready. Ready requires explicit scope, a tested version,
successful required/critical cases on that version (or reasoned non-applicability),
and no unresolved high/critical finding.

Set `project.target` to `candidate` or `deployed`. A deployed ready claim also
requires `release.status: "verified"`, `deployed_version` and evidence. If the
tested/deployed identifiers differ, explain `release.version_mapping` and preserve
supporting evidence. Text in the ledger is a recorded claim, not an authorization
grant or a proof that the mapping is true.

```bash
python3 scripts/audit_ledger.py check /tmp/my-project-audit/audit.json
python3 scripts/audit_ledger.py report /tmp/my-project-audit/audit.json
python3 scripts/audit_ledger.py manifest /tmp/my-project-audit/audit.json
```

`report` writes English Markdown source documents at `reports/security-audit.md`
and `reports/delivery-audit.md`; localize and edit them into the user's requested
final reports. It does not create Word/PDF. `manifest` hashes only referenced
evidence, without crawling private files. Both refuse to replace existing outputs
unless `--force` is explicit. Invalid ledgers exit with code 2.

These checks catch contradictions and damaged evidence. They do not verify that a
test was truly executed, detect all secrets or decide whether the audit coverage
was sufficient. Keep original test execution and human review as the authority.
