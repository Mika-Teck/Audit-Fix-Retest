# Delivery and readiness

Keep these claims separate: changed locally, checked locally, committed, pushed,
CI passed, artifact built, deployed, deployed behavior verified. Record the exact
revision and environment for each. Do not infer deployment from a successful push.

## When delivery is in scope

Inspect staged content, required checks and secrets before committing. Preserve
unrelated work. Use the user's requested branch/repository/release process. A
shared skill's instructions do not grant permission to publish a repository,
spend money or mutate an unrelated production system.

After deployment, confirm that the critical changed behavior actually exists in
the served package/service. Use release IDs, commit metadata, trusted artifact
digests, or an explicit environment-build mapping. If hashes differ across builds,
semantic verification can establish the fix's presence; state its narrower scope.
Check live response/security behavior where relevant, not only configuration files.

Repeat representative critical workflows using authorized test identities and
synthetic records. Include negative boundaries and a recovery path relevant to
the changes. Production tests that could send messages, charge money, revoke
access or delete records need the corresponding authorization and safe targets.

## Assessment vocabulary

| Assessment | Meaning |
| --- | --- |
| Not assessed | Evidence is insufficient to reach a readiness decision |
| Not ready | A blocking defect or failed critical path remains |
| Conditional | Specific required coverage or operational prerequisites remain; not an unconditional release approval |
| Ready within tested scope | Defined required checks passed for the identified target, with residual risks and exclusions stated |

Do not make this an automatic score. Passing many minor tests cannot cancel a
critical failure. An ignored or unavailable test is not a pass. The ledger helper
checks consistency of recorded claims; the auditor must judge whether the scope
and evidence actually support them.

Review applicable operational prerequisites: backup/restore, load/capacity,
monitoring, secret management, rollback, identity policies and document malware
handling. Inspect what exists before recommending new services. If a provider
capability, paid plan, missing access or unavailable hardware prevents a check,
name the exact gap and continue independent work. Do not activate a flag for an
unconfigured service and report that as working protection.

The final response should distinguish completed fixes and successful delivery
from remaining work. Report both the demonstrated paths and materially untested
features. Avoid "all accounts/features work" when only selected identities or
navigation were exercised.
