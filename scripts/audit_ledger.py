#!/usr/bin/env python3
"""Local evidence ledger and Markdown sources. Python 3.10+, no dependencies."""
from __future__ import annotations

import argparse
import copy
import hashlib
import html
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from datetime import datetime, timezone
from urllib.parse import quote

STATUSES = ("passed", "failed", "blocked", "not_tested", "not_applicable")
AREAS = ("security", "delivery", "shared")
ASSESSMENTS = ("not_assessed", "not_ready", "conditional", "ready_within_scope")
SEVERITIES = ("critical", "high", "medium", "low", "info")


class LedgerError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise LedgerError(message)


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def utcnow():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load(path):
    with Path(path).open(encoding="utf-8") as stream:
        return json.load(stream)


def write(path, data, *, replace=False):
    path = Path(path)
    require(replace or not path.exists(), f"Output exists: {path.name}; use --force if intended")
    path.parent.mkdir(parents=True, exist_ok=True)
    # Atomic same-directory replacement; partial output cannot become a valid ledger.
    fd, temporary = tempfile.mkstemp(prefix=".audit-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(data if isinstance(data, str) else json.dumps(data, indent=2, ensure_ascii=False) + "\n")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def evidence_path(root, value):
    require(nonempty(value), "Evidence path must be a nonempty relative path")
    raw = Path(value)
    require(not raw.is_absolute() and ".." not in raw.parts, "Evidence must stay inside the audit directory")
    resolved = (root / raw).resolve()
    require(resolved.is_relative_to(root.resolve()), "Evidence symlink escapes the audit directory")
    require(resolved.is_file(), f"Missing evidence file: {value}")
    return resolved


def digest(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def check_ref(root, ref):
    require(isinstance(ref, dict), "Evidence references need a path and optional sha256")
    path = evidence_path(root, ref.get("path"))
    if "sha256" in ref:
        require(ref["sha256"] == digest(path), f"Evidence changed: {ref['path']}")
    return path


def latest(case):
    return case["runs"][-1]["status"] if case.get("runs") else "not_tested"


def validate(data, root):
    require(isinstance(data, dict) and data.get("schema_version") == 1, "Expected schema_version 1")
    project = data.get("project", {})
    require(nonempty(project.get("name")), "Project name is required")
    require(project.get("target") in ("candidate", "deployed"), "Target must be candidate or deployed")
    require(isinstance(data.get("scope"), dict), "Scope is required")
    require(isinstance(data["scope"].get("coverage"), list), "scope.coverage must be a list")
    require(isinstance(data.get("cases"), list), "cases must be a list")
    require(isinstance(data.get("findings"), list), "findings must be a list")
    require(isinstance(data.get("screenshots"), list), "screenshots must be a list")
    require(isinstance(data.get("limitations"), list), "limitations must be a list")
    ids = set()
    for case in data["cases"]:
        require(isinstance(case, dict), "Each case must be an object")
        cid = case.get("id")
        require(nonempty(cid) and cid not in ids, "Case IDs must be nonempty and unique")
        ids.add(cid)
        require(case.get("area") in AREAS, f"{cid}: invalid area")
        for field in ("objective", "actor", "environment", "expected"):
            require(nonempty(case.get(field)), f"{cid}: missing {field}")
        for field in ("required", "critical"):
            require(type(case.get(field)) is bool, f"{cid}: {field} must be boolean")
        require(isinstance(case.get("runs"), list), f"{cid}: runs must be a list")
        for run in case["runs"]:
            require(isinstance(run, dict), f"{cid}: run must be an object")
            require(run.get("status") in STATUSES, f"{cid}: invalid run status")
            for field in ("at", "observed", "version"):
                require(nonempty(run.get(field)), f"{cid}: missing run {field}")
            try:
                stamp = datetime.fromisoformat(run["at"].replace("Z", "+00:00"))
                require(stamp.tzinfo is not None, f"{cid}: timestamp needs a timezone")
            except ValueError as error:
                raise LedgerError(f"{cid}: invalid timestamp") from error
            refs = run.get("evidence", [])
            require(isinstance(refs, list), f"{cid}: evidence must be a list")
            if run["status"] in ("passed", "failed"):
                require(bool(refs), f"{cid}: executed outcome requires evidence")
            if run["status"] in ("blocked", "not_tested", "not_applicable"):
                require(nonempty(run.get("reason")), f"{cid}: outcome needs a reason")
            for ref in refs:
                check_ref(root, ref)
    cases = {c["id"]: c for c in data["cases"]}
    finding_ids = set()
    for finding in data["findings"]:
        fid = finding.get("id")
        require(nonempty(fid) and fid not in finding_ids, "Finding IDs must be unique")
        finding_ids.add(fid)
        require(finding.get("area") in AREAS, f"{fid}: invalid area")
        require(finding.get("severity") in SEVERITIES, f"{fid}: invalid severity")
        require(finding.get("status") in ("open", "corrected", "not_reproduced", "excluded"), f"{fid}: invalid status")
        for field in ("title", "origin", "impact"):
            require(nonempty(finding.get(field)), f"{fid}: missing {field}")
        require(bool(finding.get("evidence")), f"{fid}: finding needs evidence")
        for ref in finding["evidence"]:
            check_ref(root, ref)
        if finding["status"] == "corrected":
            require(nonempty(finding.get("correction")), f"{fid}: missing correction")
            retests = finding.get("retest_ids", [])
            require(isinstance(retests, list) and bool(retests), f"{fid}: missing retest IDs")
            require(all(cid in cases and latest(cases[cid]) == "passed" for cid in retests), f"{fid}: retests must pass")
        if finding["status"] in ("not_reproduced", "excluded"):
            require(nonempty(finding.get("reason")), f"{fid}: disposition needs a reason")
    for shot in data["screenshots"]:
        require(shot.get("area") in AREAS, "Screenshot needs an area")
        require(shot.get("reviewed_for_secrets") is True, "Review screenshot pixels for secrets before including it")
        require(nonempty(shot.get("caption")), "Screenshot caption is required")
        path = check_ref(root, shot)
        require(path.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp"), "Unsupported screenshot format")
    assessment = data.get("assessment", {})
    state = assessment.get("status")
    require(state in ASSESSMENTS, "Invalid assessment")
    if state != "not_assessed":
        require(nonempty(assessment.get("rationale")), "Assessment needs a rationale")
    if state == "conditional":
        require(bool(assessment.get("conditions")), "Conditional assessment needs explicit conditions")
    if state in ("conditional", "ready_within_scope"):
        require(bool(cases), "Cannot assess a project with no cases")
        critical_failed = any(c["critical"] and latest(c) == "failed" for c in cases.values())
        unresolved_critical = any(f["severity"] == "critical" and f["status"] in ("open", "not_reproduced") for f in data["findings"])
        require(not critical_failed and not unresolved_critical, "A critical failure requires not_ready")
    if state == "ready_within_scope":
        require(bool(data["scope"]["coverage"]), "Ready assessment requires an explicit coverage scope")
        require(nonempty(project.get("tested_version")), "Ready assessment needs tested_version")
        required = [c for c in cases.values() if c["required"] or c["critical"]]
        require(bool(required), "Ready assessment requires required coverage")
        for case in required:
            require(latest(case) in ("passed", "not_applicable"), f"{case['id']}: required coverage is incomplete")
            if latest(case) == "passed":
                require(case["runs"][-1]["version"] == project["tested_version"], f"{case['id']}: required pass is from another version")
        blocking = [f for f in data["findings"] if f["severity"] in ("critical", "high") and f["status"] in ("open", "not_reproduced")]
        require(not blocking, "Unresolved high/critical finding prevents ready assessment")
        if project["target"] == "deployed":
            release = data.get("release", {})
            require(release.get("status") == "verified", "Deployed target needs release verification")
            require(nonempty(release.get("deployed_version")), "Missing deployed_version")
            if release["deployed_version"] != project["tested_version"]:
                require(nonempty(release.get("version_mapping")), "Different deployed/tested versions need an explicit mapping")
            require(bool(release.get("evidence")), "Missing release evidence")
            for ref in release["evidence"]:
                check_ref(root, ref)
    # Validate release evidence even when no ready declaration was made.
    for ref in data.get("release", {}).get("evidence", []):
        check_ref(root, ref)
    return data


def counts(cases):
    return {status: sum(latest(case) == status for case in cases) for status in STATUSES}


def md(value):
    value = html.escape(str(value), quote=False).replace("\n", " ")
    return re.sub(r"([\\`*_{}\[\]()#!|])", r"\\\1", value)


def relative_link(root, output, value):
    path = evidence_path(root, value)
    return quote(Path(os.path.relpath(path, output.parent.resolve())).as_posix(), safe="/-._")


def render(data, root, area, output):
    title = "Security audit" if area == "security" else "Delivery and functional acceptance audit"
    cases = [c for c in data["cases"] if c["area"] in (area, "shared")]
    findings = [f for f in data["findings"] if f["area"] in (area, "shared")]
    a, p = data["assessment"], data["project"]
    lines = [f"# {title} of {md(p['name'])}", "", f"Generated at {utcnow()}", "",
             "## Conclusion", "", f"Recorded assessment: **{md(a['status'])}**.", "",
             md(a.get("rationale") or "No readiness conclusion has been recorded."), "",
             "This is an evidence ledger report source. It is not an independent certification.", "",
             "## Scope and versions", ""]
    for label, value in [("Project type", p.get("type", "unspecified")), ("Target", p["target"]),
                         ("Baseline version", p.get("baseline_version", "not recorded")),
                         ("Tested version", p.get("tested_version", "not recorded")),
                         ("Release status", data.get("release", {}).get("status", "not_requested")),
                         ("Deployed version", data.get("release", {}).get("deployed_version", "not recorded"))]:
        lines.append(f"- {label}: {md(value)}")
    lines += ["", "Coverage:"] + [f"- {md(x)}" for x in data["scope"]["coverage"]]
    lines += ["", "Exclusions:"] + [f"- {md(x)}" for x in data["scope"].get("exclusions", [])]
    lines += ["", "## Current outcomes", "", "| Outcome | Cases |", "| --- | ---: |"]
    lines += [f"| {status} | {count} |" for status, count in counts(cases).items()]
    lines += ["", "Counts use the latest run per case; the complete history follows.", ""]
    for case in cases:
        lines += [f"## {md(case['id'])} {md(case['objective'])}", "",
                  f"Actor: {md(case['actor'])}. Environment: {md(case['environment'])}.", "",
                  f"Expected: {md(case['expected'])}.", "",
                  f"Required: {case['required']}. Critical: {case['critical']}.", ""]
        if not case["runs"]:
            lines += ["Not tested. No attempt recorded.", ""]
        for number, run in enumerate(case["runs"], 1):
            lines += [f"### Attempt {number}", "", f"{md(run['at'])} | {md(run['version'])} | **{run['status']}**", "", md(run["observed"]), ""]
            if run.get("reason"):
                lines += [f"Reason: {md(run['reason'])}", ""]
            if run.get("command"):
                lines += [f"Recorded command: {md(run['command'])}", ""]
            if "exit_code" in run:
                lines += [f"Exit code: {md(run['exit_code'])}", ""]
            for ref in run.get("evidence", []):
                lines.append(f"- Evidence: [{md(ref['path'])}]({relative_link(root, output, ref['path'])})")
            lines.append("")
    lines += ["## Findings and corrections", ""]
    if not findings:
        lines += ["No findings recorded for this report area. This does not prove absence of defects.", ""]
    for f in findings:
        lines += [f"### {md(f['id'])} {md(f['title'])}", "",
                  f"Severity: {f['severity']}. Status: {f['status']}. Origin: {md(f['origin'])}.", "", md(f["impact"]), ""]
        for key in ("correction", "reason", "residual_risk"):
            if f.get(key): lines += [f"{key.replace('_', ' ').capitalize()}: {md(f[key])}", ""]
        if f.get("retest_ids"): lines += ["Retests: " + ", ".join(md(x) for x in f["retest_ids"]), ""]
        for ref in f["evidence"]:
            lines.append(f"- Evidence: [{md(ref['path'])}]({relative_link(root, output, ref['path'])})")
        lines.append("")
    lines += ["## Remaining conditions and limitations", ""]
    for value in a.get("conditions", []) + data["limitations"]:
        lines.append(f"- {md(value)}")
    if not a.get("conditions") and not data["limitations"]:
        lines.append("No limitations recorded. The auditor must confirm that coverage exclusions are complete.")
    for shot in data["screenshots"]:
        if shot["area"] in (area, "shared"):
            lines += ["", f"![{md(shot['caption'])}]({relative_link(root, output, shot['path'])})", "", md(shot["caption"])]
    return "\n".join(lines) + "\n"


def references(data):
    for case in data["cases"]:
        for run in case["runs"]:
            yield from run.get("evidence", [])
    for finding in data["findings"]:
        yield from finding["evidence"]
    yield from data["screenshots"]
    yield from data.get("release", {}).get("evidence", [])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    init = sub.add_parser("init", help="Create an unassessed ledger")
    init.add_argument("--out", type=Path, required=True)
    init.add_argument("--project", required=True)
    init.add_argument("--type", default="unspecified")
    for name in ("check", "report", "manifest", "record"):
        item = sub.add_parser(name)
        item.add_argument("ledger", type=Path)
        if name in ("report", "manifest"): item.add_argument("--force", action="store_true")
        if name == "record":
            item.add_argument("--case", required=True)
            item.add_argument("--run", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.action == "init":
        root = args.out.resolve()
        data = {"schema_version": 1, "project": {"name": args.project, "type": args.type, "target": "candidate", "baseline_version": "", "tested_version": ""},
                "scope": {"coverage": [], "exclusions": []}, "cases": [], "findings": [], "screenshots": [], "limitations": [],
                "assessment": {"status": "not_assessed", "rationale": "", "conditions": []},
                "release": {"status": "not_requested", "deployed_version": "", "evidence": []}}
        validate(data, root)
        write(root / "audit.json", data)
        (root / "evidence").mkdir(exist_ok=True)
        (root / "reports").mkdir(exist_ok=True)
        print("Created an unassessed ledger; no tests executed.")
        return 0
    root = args.ledger.resolve().parent
    data = validate(load(args.ledger), root)
    if args.action == "record":
        data = copy.deepcopy(data)
        matches = [case for case in data["cases"] if case["id"] == args.case]
        require(len(matches) == 1, "Define the case in the coverage ledger before recording a run")
        run = load(args.run)
        run.setdefault("at", utcnow())
        for ref in run.get("evidence", []):
            ref["sha256"] = digest(check_ref(root, ref))
        matches[0]["runs"].append(run)
        if data["assessment"]["status"] != "not_assessed":
            data.setdefault("assessment_history", []).append({"at": utcnow(), **data["assessment"]})
            data["assessment"] = {"status": "not_assessed", "rationale": "New evidence recorded; reassessment required.", "conditions": []}
        for finding in data["findings"]:
            if finding["status"] == "corrected" and args.case in finding.get("retest_ids", []) and latest(matches[0]) != "passed":
                finding["status"] = "open"
                finding["reopened_at"] = utcnow()
        validate(data, root)
        write(args.ledger, data, replace=True)
        print("Appended run with evidence hashes; previous attempts preserved.")
    elif args.action == "check":
        print(json.dumps({"ledger_valid": True, "recorded_assessment": data["assessment"]["status"], "current_outcomes": counts(data["cases"])}))
    elif args.action == "report":
        require((root / "reports").resolve().is_relative_to(root), "Report directory escapes the audit directory")
        outputs = [(area, root / "reports" / f"{area}-audit.md") for area in ("security", "delivery")]
        for _, output in outputs:
            require(args.force or not output.exists(), f"Output exists: {output.name}; use --force if intended")
        for area, output in outputs:
            write(output, render(data, root, area, output), replace=args.force)
        print("Wrote two Markdown sources. Word/PDF generation and visual QA remain separate.")
    else:
        unique = {ref["path"]: check_ref(root, ref) for ref in references(data)}
        files = [{"path": name, "bytes": path.stat().st_size, "sha256": digest(path)} for name, path in sorted(unique.items())]
        write(root / "evidence-manifest.json", {"generated_at": utcnow(), "files": files}, replace=args.force)
        print(f"Hashed {len(files)} referenced evidence files; no other files scanned.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (LedgerError, OSError, ValueError, TypeError, KeyError) as error:
        print(f"Ledger error: {error}", file=sys.stderr)
        sys.exit(2)
