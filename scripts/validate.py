#!/usr/bin/env python3
"""Validate data/trainings.json and data/learning_path.json.

Checks the JSON Schema, then the rules the schema cannot express:
unique IDs, duplicate offerings, rating classes, suitability arithmetic,
EUR conversion, dates and learning-path references.

Use --check-generated to also fail when catalogue/ is stale.
Exit status is non-zero on any error; warnings do not fail the run.
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from collections import defaultdict

from jsonschema import Draft202012Validator

from common import (
    DB_PATH, MISSING, PATH_PATH, SCHEMA_PATH, eur_for, expected_rating_class,
    load_json, norm, norm_url, weighted_score,
)


def validate(db: dict, path: dict | None) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    schema = load_json(SCHEMA_PATH)
    validator = Draft202012Validator(schema, format_checker=Draft202012Validator.FORMAT_CHECKER)
    for err in sorted(validator.iter_errors(db), key=lambda e: list(e.path)):
        loc = "/".join(str(p) for p in err.path)
        errors.append(f"schema: {loc}: {err.message}")
    if errors:
        return errors, warnings

    today = dt.date.today().isoformat()
    ids: dict[str, int] = defaultdict(int)
    urls: dict[str, list[str]] = defaultdict(list)
    names: dict[str, list[str]] = defaultdict(list)

    for rec in db["records"]:
        rid = rec["id"]
        ids[rid] += 1
        if rec["status"] != "archived":
            urls[norm_url(rec["official_url"])].append(rid)
            names[norm(rec["provider"]) + "|" + norm(rec["title"])].append(rid)

        rating = rec["learner_rating"]
        expected = expected_rating_class(rating)
        if expected is None:
            if rec["rating_class"] != "credible-but-unrated":
                errors.append(f"{rid}: no published rating, so rating_class must be credible-but-unrated")
        elif rec["rating_class"] != expected:
            errors.append(f"{rid}: rating_class {rec['rating_class']} but rating implies {expected}")
        if rating["status"] == "published":
            if rating["value"] > rating["scale"]:
                errors.append(f"{rid}: rating value exceeds scale")
            if rating["verified_on"] > today:
                errors.append(f"{rid}: rating verified_on is in the future")

        suit = rec["suitability"]
        want = weighted_score(suit["components"])
        if suit["score"] != want:
            errors.append(f"{rid}: suitability score {suit['score']} != weighted components {want}")

        eur = eur_for(rec["pricing"], db["fx"])
        if rec["pricing"]["eur_approx"] != eur:
            errors.append(f"{rid}: eur_approx {rec['pricing']['eur_approx']!r} != {eur!r}; run scripts/apply_fx.py")
        if rec["pricing"]["model"] == "free" and rec["pricing"]["amount"] not in (0, *MISSING):
            errors.append(f"{rid}: pricing model is free but amount is {rec['pricing']['amount']}")

        hours = rec["delivery"]["study_hours"]
        if isinstance(hours["min"], (int, float)) and isinstance(hours["max"], (int, float)):
            if hours["min"] > hours["max"]:
                errors.append(f"{rid}: study_hours min > max")

        if rec["verification"]["last_verified"] > today:
            errors.append(f"{rid}: last_verified is in the future")
        dates = [h["date"] for h in rec["history"]]
        if dates != sorted(dates):
            errors.append(f"{rid}: history is not in date order")

        if rec["user"].get("completion_status") == "completed" and "completed_on" not in rec["user"]:
            warnings.append(f"{rid}: completed but completed_on is not set")
        age = (dt.date.today() - dt.date.fromisoformat(rec["verification"]["last_verified"])).days
        if rec["status"] != "archived" and age > 180:
            warnings.append(f"{rid}: last verified {age} days ago; refresh it")

    for rid, count in ids.items():
        if count > 1:
            errors.append(f"duplicate id: {rid}")
    for url, rids in urls.items():
        if len(rids) > 1:
            errors.append(f"possible duplicate offering (same official URL {url}): {', '.join(rids)}")
    for key, rids in names.items():
        if len(rids) > 1:
            errors.append(f"possible duplicate offering (same provider and title): {', '.join(rids)}")

    if path is not None:
        known = set(ids)
        archived = {r["id"] for r in db["records"] if r["status"] == "archived"}
        for stage in path["stages"]:
            for step in stage["steps"]:
                if step["id"] not in known:
                    errors.append(f"learning_path: unknown record id {step['id']}")
                elif step["id"] in archived:
                    warnings.append(f"learning_path: {step['id']} is archived")
                for extra in step.get("extra_costs", []):
                    ok = (
                        isinstance(extra.get("amount"), (int, float))
                        and (extra.get("currency") == "EUR" or extra.get("currency") in db["fx"]["rates"])
                        and extra.get("description")
                    )
                    if not ok:
                        errors.append(f"learning_path: bad extra_costs entry on {step['id']}: {extra}")

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check-generated", action="store_true", help="fail if catalogue/ is out of date")
    args = parser.parse_args()

    db = load_json(DB_PATH)
    path = load_json(PATH_PATH) if PATH_PATH.exists() else None
    errors, warnings = validate(db, path)

    if args.check_generated and not errors:
        import build_catalogue
        stale = build_catalogue.stale_outputs(db, path)
        errors.extend(f"generated file is stale: {name}; run scripts/build_catalogue.py" for name in stale)

    for w in warnings:
        print(f"WARNING {w}")
    for e in errors:
        print(f"ERROR {e}")
    active = sum(1 for r in db["records"] if r["status"] != "archived")
    print(f"{len(db['records'])} records ({active} not archived): {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
