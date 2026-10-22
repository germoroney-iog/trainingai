#!/usr/bin/env python3
"""Merge refreshed or new records into data/trainings.json without losing manual data.

Usage:
  scripts/upsert.py candidates.json [--date YYYY-MM-DD] [--dry-run]
  scripts/upsert.py --archive ID --reason "Withdrawn by provider" [--superseded-by ID]

candidates.json is {"records": [...]} using the same schema. Each candidate is
matched to an existing record by id, then official URL, then provider + title.
On a match the existing id, user block and history are kept, material changes
are appended to history, and every other field is replaced by the candidate.
Unmatched candidates are added as new records. Records are never deleted:
archive them instead.
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

from common import DB_PATH, dump_json, eur_for, load_json, norm, norm_url

MATERIAL = {
    "title": lambda r: r["title"],
    "official URL": lambda r: r["official_url"],
    "status": lambda r: r["status"],
    "advertised price": lambda r: r["pricing"]["advertised"],
    "pricing model": lambda r: r["pricing"]["model"],
    "credential type": lambda r: r["credential"]["type"],
    "start dates": lambda r: r["delivery"]["start_dates"],
    "learner rating": lambda r: (
        f"{r['learner_rating']['value']}/{r['learner_rating']['scale']} from "
        f"{r['learner_rating']['review_count']} {r['learner_rating']['count_type']}"
        if r["learner_rating"]["status"] == "published" else r["learner_rating"]["status"]
    ),
    "suitability": lambda r: r["suitability"]["score"],
}


def find_match(db_records, cand):
    for key in (
        lambda r: r["id"],
        lambda r: norm_url(r["official_url"]),
        lambda r: norm(r["provider"]) + "|" + norm(r["title"]),
    ):
        hits = [r for r in db_records if key(r) == key(cand)]
        if hits:
            return hits[0]
    return None


def merge(existing: dict, cand: dict, date: str) -> list[str]:
    changes = [
        f"{label} changed from {get(existing)!r} to {get(cand)!r}"
        for label, get in MATERIAL.items()
        if get(existing) != get(cand)
    ]
    keep = {k: existing[k] for k in ("id", "user", "history")}
    existing.clear()
    existing.update(cand)
    existing.update(keep)
    entry = "Re-verified." if not changes else "Re-verified. " + "; ".join(changes) + "."
    existing["history"].append({"date": date, "change": entry})
    existing["verification"]["last_verified"] = date
    return changes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("candidates", nargs="?")
    parser.add_argument("--date", default=dt.date.today().isoformat())
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--archive", metavar="ID")
    parser.add_argument("--reason")
    parser.add_argument("--superseded-by")
    args = parser.parse_args()

    db = load_json(DB_PATH)
    by_id = {r["id"]: r for r in db["records"]}

    if args.archive:
        if not args.reason:
            parser.error("--archive needs --reason")
        rec = by_id.get(args.archive)
        if rec is None:
            parser.error(f"unknown id {args.archive}")
        rec["status"] = "archived"
        rec["archive"] = {"date": args.date, "reason": args.reason}
        if args.superseded_by:
            rec["archive"]["superseded_by"] = args.superseded_by
        rec["history"].append({"date": args.date, "change": f"Archived: {args.reason}"})
        print(f"archived {args.archive}")
    elif args.candidates:
        added = updated = 0
        for cand in load_json(Path(args.candidates))["records"]:
            cand["pricing"]["eur_approx"] = eur_for(cand["pricing"], db["fx"])
            match = find_match(db["records"], cand)
            if match is None:
                if cand["id"] in by_id:
                    print(f"ERROR new record reuses existing id {cand['id']}", file=sys.stderr)
                    return 1
                cand.setdefault("user", {"completion_status": "not-started", "notes": ""})
                cand.setdefault("history", [{"date": args.date, "change": "Record created."}])
                db["records"].append(cand)
                by_id[cand["id"]] = cand
                added += 1
                print(f"added   {cand['id']}")
            else:
                changes = merge(match, cand, args.date)
                updated += 1
                print(f"updated {match['id']}: {'; '.join(changes) or 'no material change'}")
        print(f"{added} added, {updated} updated")
    else:
        parser.error("give a candidates file or --archive")

    db["updated_on"] = args.date
    if args.dry_run:
        print("dry run: nothing written")
    else:
        dump_json(DB_PATH, db)
    return 0


if __name__ == "__main__":
    sys.exit(main())
