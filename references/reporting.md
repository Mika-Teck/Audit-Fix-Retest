# From evidence to final reports

## Source of truth

Keep a ledger or equivalent project test records. For each meaningful attempt,
record scenario/actor/environment/version, expected outcome, observation, status,
time and evidence. Distinguish passed, failed, blocked, not tested and not
applicable. Count current outcomes separately from the history of attempts.

For each finding include origin (reproduction, inspection or scanner), severity
with rationale, impact, sanitized before evidence, correction/change reference,
retest and remaining risk. Record a harness repair separately from a product
repair. Do not quietly remove its earlier failure from the history.

The optional helper generates **Markdown sources**, not final Word/PDF files and
not an independent security certification. It preserves recorded run history,
checks referenced local evidence and rejects unsupported readiness declarations.
Screenshots are included only after the auditor records a manual privacy review.

## Two reports by default

The security report explains relevant trust boundaries, vulnerabilities/configuration
warnings, corrected findings, actual denial tests, dependency results and residual
risks. Keep scanner counts separate from confirmed exploitable defects.

The delivery report explains real accounts/actors exercised, workflow and negative
branches, persistence and recovery, generated artifacts, deployed version/CI
checks and feature coverage. Opening a route is navigation evidence, not proof of
its mutations. For non-UI projects, show commands, API traces or output artifacts.

Both should open with the conclusion and what it means for the project owner.
State scope, dates, versions and environments before detailed results. Include an
evidence register and the limits of the audit. Do not inflate length or hide a
failed required scenario in an appendix.

## Evidence hygiene

- Keep credentials, tokens, codes, service keys and private connection strings out
  of reports, screenshots, source examples and public archives. Use private files
  or an existing secret store at execution time, never copied project secrets.
- Use screenshots from actual executions. Prefer synthetic records; remove or
  redact unrelated personal information. Inspect screenshot pixels, not just filenames.
- Use stable, distinct filenames per attempt. Store sanitized evidence separately
  from raw logs. A failing screenshot can be useful if labelled as the before state.
- Preserve download/generated-file bytes when authorized, and inspect the actual
  output. A generation API's success response does not prove a valid document.
- Hash retained evidence to identify it and detect later changes. Hashes establish
  file identity, not that an observation was correct or performed on a claimed version.
- Do not upload private evidence or reports to a public repository unless the user
  has authorized that disclosure. Sharing the skill itself does not authorize
  sharing the project's audit data.

## Word and PDF

Use available document/PDF tooling and follow its instructions. In a different
environment, discover suitable tools rather than copying absolute runtime paths.
For example, a Word authoring library plus an installed Word/LibreOffice exporter
can produce equivalent formats; a PDF renderer can produce page images for QA.
Install/download dependencies only within the host's permissions and task scope.

Create editable Word reports with readable hierarchy, appropriately sized tables,
captions and real evidence images. Export each final Word file to PDF when
possible so both formats agree. Render the final artifacts and inspect every page
for clipping, broken tables, missing glyphs, secrets in images and orphaned captions.
Repeat rendering after corrections. Text extraction alone is insufficient.

If the formats use independent rendering engines, compare their substantive
content as well as layout. Reopen the delivered copies, confirm page counts,
embedded figures, versions and absence of sensitive values. Return only requested
final artifacts; keep diagnostic images and builders out of the public package.

When conversion or visual verification is unavailable, deliver the available
sources if useful and state exactly which outputs remain incomplete. Do not
rename Markdown/HTML as DOCX/PDF or claim a file exists because a converter started.
