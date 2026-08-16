#!/usr/bin/env python3
"""Validate the DSB DevSecOps engineering rule catalog.

Checks every rule file in rules/ for schema conformance so that malformed or
drifting rules cannot reach a release. Run it directly, or via CI:

    uv run --with pyyaml python scripts/validate_rules.py

Exit code 0 on success, 1 on any validation failure.
"""

from __future__ import annotations

import sys
from pathlib import Path

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover - environment guard
    sys.exit(
        "PyYAML is required.\n"
        "  pip install pyyaml            # or\n"
        "  uv run --with pyyaml python scripts/validate_rules.py"
    )

RULES_DIR = Path(__file__).resolve().parent.parent / "rules"

# The four delivery phases, plus 'cross-cutting' for governance rules that
# constrain the pipeline as a whole rather than one phase of it.
ALLOWED_PHASES = {"build", "test", "scan", "deploy", "cross-cutting"}

# N/A is a runtime outcome recorded per workload (DSB-EVD-003), never a
# per-rule default, so it is not a valid value here.
ALLOWED_ENFORCEMENT_LEVELS = {"block", "warn", "report"}

REQUIRED_FRAMEWORK_KEYS = {
    "nist_ssdf",
    "slsa",
    "owasp_cicd",
    "owasp_samm",
    "cncf_supply_chain",
}

REQUIRED_RULE_FIELDS = (
    "id",
    "title",
    "phase",
    "requirement",
    "rationale",
    "applicability",
    "framework_mappings",
    "enforcement",
    "tooling",
)

# Family -> expected rule count. Guards against accidental additions or
# deletions; update deliberately alongside a CHANGELOG entry.
EXPECTED_FAMILIES = {
    "DSB-BUILD": 4,
    "DSB-TEST": 3,
    "DSB-SCAN": 10,
    "DSB-DEPLOY": 4,
    "DSB-ID": 3,
    "DSB-SRC": 3,
    "DSB-SC": 3,
    "DSB-ART": 4,
    "DSB-IAC": 3,
    "DSB-EVD": 3,
    "DSB-EXC": 2,
}
EXPECTED_TOTAL = sum(EXPECTED_FAMILIES.values())


def validate_rule(rule: dict, family: str, path: Path, errors: list[str]) -> str | None:
    """Validate one rule; return its id if usable for uniqueness checks."""
    where = f"{path.name}"
    rule_id = rule.get("id", "<missing id>")

    for field in REQUIRED_RULE_FIELDS:
        if field not in rule:
            errors.append(f"{where}: {rule_id}: missing required field '{field}'")

    if not isinstance(rule_id, str) or not rule_id.startswith(f"{family}-"):
        errors.append(f"{where}: rule id '{rule_id}' does not carry family prefix '{family}-'")

    for field in ("title", "requirement", "rationale"):
        value = rule.get(field)
        if field in rule and (not isinstance(value, str) or not value.strip()):
            errors.append(f"{where}: {rule_id}: '{field}' must be a non-empty string")

    phase = rule.get("phase")
    if "phase" in rule and phase not in ALLOWED_PHASES:
        errors.append(
            f"{where}: {rule_id}: phase '{phase}' not in {sorted(ALLOWED_PHASES)}"
        )

    applicability = rule.get("applicability")
    if "applicability" in rule:
        if not isinstance(applicability, dict):
            errors.append(f"{where}: {rule_id}: 'applicability' must be a mapping")
        else:
            if not isinstance(applicability.get("always"), bool):
                errors.append(f"{where}: {rule_id}: applicability.always must be a boolean")
            for key in ("conditions", "not_applicable_when"):
                if not isinstance(applicability.get(key), list):
                    errors.append(f"{where}: {rule_id}: applicability.{key} must be a list")
            if applicability.get("always") is False and not applicability.get("conditions"):
                errors.append(
                    f"{where}: {rule_id}: conditional rule must state at least one condition"
                )

    mappings = rule.get("framework_mappings")
    if "framework_mappings" in rule:
        if not isinstance(mappings, dict):
            errors.append(f"{where}: {rule_id}: 'framework_mappings' must be a mapping")
        else:
            missing = REQUIRED_FRAMEWORK_KEYS - set(mappings)
            unknown = set(mappings) - REQUIRED_FRAMEWORK_KEYS
            if missing:
                errors.append(
                    f"{where}: {rule_id}: framework_mappings missing keys {sorted(missing)}"
                )
            if unknown:
                errors.append(
                    f"{where}: {rule_id}: framework_mappings has unknown keys {sorted(unknown)}"
                )
            for key, value in mappings.items():
                if not isinstance(value, list):
                    errors.append(
                        f"{where}: {rule_id}: framework_mappings.{key} must be a list"
                    )

    enforcement = rule.get("enforcement")
    if "enforcement" in rule:
        if not isinstance(enforcement, dict):
            errors.append(f"{where}: {rule_id}: 'enforcement' must be a mapping")
        else:
            level = enforcement.get("level")
            if level not in ALLOWED_ENFORCEMENT_LEVELS:
                errors.append(
                    f"{where}: {rule_id}: enforcement.level '{level}' not in "
                    f"{sorted(ALLOWED_ENFORCEMENT_LEVELS)}"
                )
            if not isinstance(enforcement.get("automatable"), bool):
                errors.append(f"{where}: {rule_id}: enforcement.automatable must be a boolean")

    tooling = rule.get("tooling")
    if "tooling" in rule:
        if not isinstance(tooling, dict):
            errors.append(f"{where}: {rule_id}: 'tooling' must be a mapping")
        else:
            if not isinstance(tooling.get("examples"), list):
                errors.append(f"{where}: {rule_id}: tooling.examples must be a list")
            # Capability-based, never vendor-based: the preference for an existing
            # organizational tool is a property of every rule in the catalog.
            if tooling.get("prefer_existing_tool") is not True:
                errors.append(
                    f"{where}: {rule_id}: tooling.prefer_existing_tool must be true"
                )

    return rule_id if isinstance(rule_id, str) else None


def main() -> int:
    errors: list[str] = []
    seen_ids: dict[str, str] = {}
    counts: dict[str, int] = {}

    rule_files = sorted(RULES_DIR.glob("*.yaml"))
    if not rule_files:
        print(f"FAIL: no rule files found in {RULES_DIR}")
        return 1

    for path in rule_files:
        try:
            doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            errors.append(f"{path.name}: YAML parse error: {exc}")
            continue

        if not isinstance(doc, dict):
            errors.append(f"{path.name}: top level must be a mapping")
            continue

        family = doc.get("family")
        if not isinstance(family, str) or not family.startswith("DSB-"):
            errors.append(f"{path.name}: 'family' must be a DSB-prefixed string")
            continue
        if not isinstance(doc.get("scope"), str) or not doc.get("scope", "").strip():
            errors.append(f"{path.name}: 'scope' must be a non-empty string")

        rules = doc.get("rules")
        if not isinstance(rules, list) or not rules:
            errors.append(f"{path.name}: 'rules' must be a non-empty list")
            continue

        for rule in rules:
            if not isinstance(rule, dict):
                errors.append(f"{path.name}: every rule must be a mapping")
                continue
            rule_id = validate_rule(rule, family, path, errors)
            if rule_id:
                if rule_id in seen_ids:
                    errors.append(
                        f"{path.name}: duplicate rule id '{rule_id}' "
                        f"(already defined in {seen_ids[rule_id]})"
                    )
                else:
                    seen_ids[rule_id] = path.name

        counts[family] = counts.get(family, 0) + len(rules)

    for family, expected in EXPECTED_FAMILIES.items():
        actual = counts.get(family)
        if actual is None:
            errors.append(f"family {family} is missing from the catalog")
        elif actual != expected:
            errors.append(f"family {family}: expected {expected} rules, found {actual}")
    for family in set(counts) - set(EXPECTED_FAMILIES):
        errors.append(f"unexpected family '{family}' — add it to EXPECTED_FAMILIES first")

    total = sum(counts.values())

    if errors:
        print(f"FAIL: {len(errors)} validation error(s)\n")
        for error in errors:
            print(f"  - {error}")
        return 1

    print(f"OK — {total} rules across {len(counts)} families")
    for family in sorted(counts, key=lambda f: (-counts[f], f)):
        print(f"  {family:<12} {counts[family]:>2}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
