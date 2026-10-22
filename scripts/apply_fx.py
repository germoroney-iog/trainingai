#!/usr/bin/env python3
"""Recompute pricing.eur_approx for every record from the top-level fx block.

Update data/trainings.json "fx" (source, URL, rate date, rates) first, then run
this script. Only eur_approx is touched.
"""

from __future__ import annotations

import sys

from common import DB_PATH, dump_json, eur_for, load_json


def main() -> int:
    db = load_json(DB_PATH)
    changed = 0
    for rec in db["records"]:
        new = eur_for(rec["pricing"], db["fx"])
        if rec["pricing"].get("eur_approx") != new:
            rec["pricing"]["eur_approx"] = new
            changed += 1
    dump_json(DB_PATH, db)
    print(f"eur_approx updated on {changed} record(s) using rates dated {db['fx']['rate_date']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
