---
name: audit-fix-retest
description: "Audit a software project's security and delivery workflows, fix defects, retest them, and produce evidence-based reports. Use for requested audits, acceptance testing or production-readiness reviews across stacks; not for every ordinary code change."
---

# Audit Fix Retest

Turn an authorized audit into verified corrections and reviewable reports. Adapt to
the project's language, runtime, interfaces and deployment model. Report in the
user's language. A passing build, an open screen and a successful deployment each
prove different things.

## Establish the target

Read repository instructions and discover the real entry points, test commands,
roles, state transitions, dependencies and services. Use the project's maintained
tools rather than assuming npm, a database vendor, a browser or a cloud provider.

Identify the version under test and whether the target is a release candidate or
an already deployed system. Make a short, risk-based coverage matrix before
running tests: actor, environment, action, expected result, required coverage and
evidence. Include failure/recovery paths and unauthorized callers where relevant.
For a library or CLI, substitute public API/command contracts for pages; for a
data pipeline, use input/output invariants and replay behavior. Hardware or services
that cannot be reached remain explicit coverage gaps.

Carry forward authorization already given. Audit/fix authorization does not by
itself authorize purchases, real payments, messages to other people, destructive
data operations or public publication. Use synthetic records and authorized
accounts. Ask only for missing access or a material scope choice; continue
independent work while waiting. Never store credentials in the audit ledger.

Read [audit-method.md](references/audit-method.md) when selecting controls and
exercising real accounts, services, migrations or business workflows.

## Test, correct and retest

1. Capture a baseline and reproduce each suspected defect at the boundary where
   it matters. Record the expected and observed result, actor, version, environment
   and sanitized evidence. Label scanner warnings and code-review findings as
   such when no exploit has been exercised.
2. Determine whether the failure belongs to the product, the test harness, test
   data, permissions or the environment. An assertion expecting the wrong denial
   code is a harness defect; a transport timeout is not a successful authorization
   refusal. Do not convert either into a product pass without a retest.
3. Correct the root cause within scope. Preserve business controls. Do not force
   workflow states, insert fictitious successful results, weaken authorization,
   skip failing assertions or suppress scanners to make the audit green.
4. Repeat the original scenario with its meaningful preconditions and expected
   outcome preserved. Check nearby boundaries affected by the fix, then the
   repository's required checks. Add durable regression coverage when it prevents
   a meaningful recurrence; do not create tests that merely repeat implementation.
5. Keep the failed attempt and the new result. A corrected finding needs a clear
   change and a passing retest linked to it. A static finding can be corrected
   without executing a dangerous exploit: preserve the original inspection and
   verify the relevant permission or invariant safely.

Do not blindly retry mutations after an ambiguous timeout. First inspect whether
the original operation succeeded and whether retry/idempotency is safe. After two
unsuccessful repetitions of the same approach, change the diagnosis or tool. Stop
dependent operations if they risk real data, account lockout or duplicate external
effects. Record the blocker and continue unaffected coverage.

Use realistic fixtures: a document that parses and renders, valid input formats,
and separate identities for isolation tests. A minimal magic-byte stub does not
prove a viewer works. Keep fault injection isolated and restore temporary account
or environment settings; record any state that could not be restored.

## Keep evidence usable

Use a task-local audit directory outside committed application code. Preserve
original logs privately if needed and use sanitized copies for reports. Give each
attempt its own evidence filename so a later success cannot overwrite the failure.
Screenshots must come from actual observations and be reviewed for secrets and
unrelated personal data. Capture output, traces or artifacts when there is no UI;
do not invent screenshots to fill a template.

The optional standard-library helper manages a local ledger and Markdown report
sources. It never runs project commands, accesses a network, changes application
state, deploys, or certifies actual production readiness.

```bash
python3 scripts/audit_ledger.py init --out /path/to/audit --project "Project name" --type api
# Populate coverage, environments and cases in /path/to/audit/audit.json.
python3 scripts/audit_ledger.py record /path/to/audit/audit.json --case T01 --run /path/to/run.json
python3 scripts/audit_ledger.py check /path/to/audit/audit.json
python3 scripts/audit_ledger.py report /path/to/audit/audit.json
python3 scripts/audit_ledger.py manifest /path/to/audit/audit.json
```

Read [ledger.md](references/ledger.md) only when using this helper. Existing project
test reports or an equivalent evidence ledger are equally acceptable. Do not
replace a useful project framework to adopt this helper.

## Verify delivery separately

When commit/push or deployment is requested, finish authorized changes and checks,
inspect what will be committed for secrets, then perform the requested delivery.
Respect existing work and repository conventions. Track the exact tested revision
and the CI result. A Git push does not establish that production serves that code.

For a deployed target, verify the actual release/artifact and repeat representative
critical paths there using safe test data. Different environment builds may have
different hashes: require a trustworthy artifact mapping or inspect the changed
behavior, not just HTTP 200 or a filename guess. If only local execution is
available, report local validation and the unverified deployment distinctly.

Read [release-readiness.md](references/release-readiness.md) when assessing release
readiness, deploying or closing the audit.

## Deliver the reports

Unless the user requests a different scope or format, produce two detailed reports:
a security audit and a delivery/functional acceptance audit, each in Word and PDF.
Include actual screenshots where relevant, scope, tested versions/environments,
coverage, findings, corrections, retests, remaining risks and evidence references.
Scale length to the evidence; do not pad a small CLI audit into a website report.

Read [reporting.md](references/reporting.md) for the evidence-to-report workflow.
Use installed document/PDF skills or suitable local tools when available. The
skill has no mandatory browser, connector or artifact-service dependency. If a
required output format cannot be generated or rendered, preserve the report
sources, identify the missing capability and mark the deliverable incomplete.

Close with the concrete result, delivery status, report paths and material
remaining work. Avoid an unconditional "ready for production" when required
coverage is missing or a blocking issue remains. Do not claim that every feature
works because every menu opened, or that zero dependency alerts means zero risk.
