# Selecting and exercising controls

## Discover contracts before commands

Inspect the repository instructions, manifests, CI, runbooks and service topology.
Identify the actual consumer: end user, API client, operator, downstream package,
batch scheduler or device. Derive tests from its contracts and the project's
business rules, not from a universal list of pages.

Classify environments precisely. A localhost frontend connected to a live database
is a hybrid live test. A sandboxed payment service is not a real payment. Keep
versions and observations attached to their environment.

Prioritize exposed/sensitive paths, irreversible decisions, changed components and
dependencies they rely on. Maintain a coverage matrix; mark irrelevant controls
not applicable with a reason rather than counting them as passed.

| Project | Useful boundaries and evidence |
| --- | --- |
| Web, desktop, mobile | Real actions, persistence after restart/reload, role boundaries, recovery, screenshots |
| API, service | Schemas, authentication, ownership, state transitions, error contracts, retries, response traces |
| CLI, library | Arguments/public API, exit codes, stdout/stderr, files, backward compatibility, packaging |
| Data or ML pipeline | Input validation, missing/corrupt data, deterministic invariants, lineage, replay and output correctness |
| Infrastructure | Plan/diff, identity policy, deployment identity, health, recovery evidence within authorized resources |
| Embedded/device | Simulator versus physical-device coverage, unavailable hardware, protocol and safety limits |

## Security scope

Choose relevant controls. Do not require every project to use accounts, databases,
cloud storage or e-mail.

- Authentication/session: account state, logout/revocation behavior, expiration,
  challenge replay and cross-session boundaries when a second factor exists.
  Verify enforcement at the server or protected operation, not only in the UI.
- Authorization: another owner, unrelated role, inactive account, direct endpoint
  or library call, privileged internal functions, administrative and system-only
  operations. Check data read and mutation separately.
- Inputs and outputs: injection/escaping where applicable, parsers, file type and
  size, content signatures, path handling, export content, confidential previews,
  download token reuse and error leakage. A file signature is not antivirus.
- Dependencies/configuration: maintained scanner results with versions and dates,
  exposed secrets, seed defaults, transport configuration and relevant provider
  advisories. Separate actual vulnerabilities from informational exposure warnings.
- Traceability: important actions observable without exposing secrets; failure
  paths should not silently claim success.

Use authoritative current vendor documentation for unfamiliar/version-sensitive
behavior. Record scanner name/version, command, scope and counts. A fix that only
turns a scanner off is not remediation. An intentionally public function still
needs a rationale and safe output, not a blanket dismissal of its warning.

## Real actors and workflows

Model representative valid paths and invalid transitions. For an approval system,
test who may submit, request revisions, review, approve, issue, notify and archive.
For other projects replace these with its own states and invariants.

Exercise relevant conditional paths: missing requirements, requested fields only,
fresh document replacement, conflict or self-review, independent reviewers, quorum,
mandatory reasons, immutable submitted output, duplicate requests and recovery.
The numbers/roles come from the project's rules; never impose two reviewers or a
five-person quorum on an unrelated system.

Use ordinary actor permissions and normal APIs. Direct API setup is acceptable
when that API is a supported path; disclose which actions were browser interactions
and which were API-based. Administrative database setup or state injection may
test an isolated unit but cannot prove the normal end-to-end workflow.

After a revision, verify both editable payload and derived/current metadata.
Then inspect the downstream artifact: a corrected UI title is insufficient if
the issued document reads an older database column. Similarly, extract and render
localized output; switching the interface language does not prove each generated
document uses its own locale.

## External services and uncertain outcomes

Keep recipients and destinations limited to authorized test targets. Do not drain
an entire historical queue to test one campaign. Scope jobs to the test record
and inspect outbox/result state before retrying after a timeout.

Record distinct proof levels: request queued, provider accepted, delivered,
recipient confirmed, challenge consumed. A provider's acceptance is not proof of
inbox receipt. A user-supplied code proves only the message/challenge it belongs
to. Redact codes and tokens in deliverables.

Account/password rotations and security enrollment can affect other sessions or
tests. Use them only within authorization, keep replacement secrets privately
recoverable and update authorized CI secrets if necessary. Do not reset supplied
user passwords as a routine audit step. Avoid parallel tests that temporarily
disable or mutate the same identity.

## Migrations, failures and recovery

Read the authoritative migration ledger before applying changes. Distinguish local
file history, recorded remote versions and actual schema state. Never blindly
replay old migrations or mark unknown versions applied to make a command green.
Preserve original sources when reconciling a known history discrepancy. Use the
project/vendor's migration generator, inspection and dry-run facilities.

For a failure, preserve the first trace and identify its layer. Refreshing an
obsolete development cache is an environment repair; it does not prove a product
fix. Correct malformed fixtures and selectors, then repeat the user-facing
assertion. If a defect cannot safely be fixed, document it and stop dependent
qualification instead of lowering the gate.
