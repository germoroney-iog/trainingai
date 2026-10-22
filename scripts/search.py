#!/usr/bin/env python3
"""Search the training database from the command line.

Examples:
  scripts/search.py governance
  scripts/search.py --category rag-evals-llmops --free
  scripts/search.py --level advanced --max-eur 1000 --min-score 70
  scripts/search.py --credential professional-certification --sort cost
  scripts/search.py --status in-progress          # your own completion status
"""

from __future__ import annotations

import argparse
import sys

from common import CATEGORY_LABELS, DB_PATH, FREE_MODELS, MISSING, load_json


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("text", nargs="*", help="words to find in title, provider, outcomes or relevance")
    ap.add_argument("--category", choices=sorted(CATEGORY_LABELS))
    ap.add_argument("--level")
    ap.add_argument("--free", action="store_true", help="free, free audit or publicly funded only")
    ap.add_argument("--paid", action="store_true")
    ap.add_argument("--max-eur", type=float, help="headline cost ceiling in EUR (unknown costs excluded)")
    ap.add_argument("--max-hours", type=float, help="upper study-hour estimate ceiling")
    ap.add_argument("--min-score", type=int, default=0)
    ap.add_argument("--credential", help="credential type, e.g. professional-certification")
    ap.add_argument("--highly-rated", action="store_true")
    ap.add_argument("--status", help="your completion status, e.g. planned")
    ap.add_argument("--include-archived", action="store_true")
    ap.add_argument("--sort", choices=["score", "cost", "hours"], default="score")
    args = ap.parse_args()

    rows = []
    for r in load_json(DB_PATH)["records"]:
        if r["status"] == "archived" and not args.include_archived:
            continue
        free = r["pricing"]["model"] in FREE_MODELS
        eur = r["pricing"]["eur_approx"]
        hi = r["delivery"]["study_hours"]["max"]
        blob = " ".join([r["title"], r["provider"], r["relevance"], *r["learning_outcomes"]]).lower()
        if any(w.lower() not in blob for w in args.text):
            continue
        if args.category and args.category not in r["categories"]:
            continue
        if args.level and args.level not in r["level"]:
            continue
        if (args.free and not free) or (args.paid and free):
            continue
        if args.max_eur is not None and (eur in MISSING or eur > args.max_eur):
            continue
        if args.max_hours is not None and (hi in MISSING or hi > args.max_hours):
            continue
        if r["suitability"]["score"] < args.min_score:
            continue
        if args.credential and r["credential"]["type"] != args.credential:
            continue
        if args.highly_rated and r["rating_class"] != "highly-rated":
            continue
        if args.status and r["user"]["completion_status"] != args.status:
            continue
        rows.append(r)

    def key(r):
        if args.sort == "cost":
            e = r["pricing"]["eur_approx"]
            return (e in MISSING, 0 if e in MISSING else e)
        if args.sort == "hours":
            h = r["delivery"]["study_hours"]["max"]
            return (h in MISSING, 0 if h in MISSING else h)
        return (-r["suitability"]["score"],)

    for r in sorted(rows, key=key):
        eur = r["pricing"]["eur_approx"]
        model = r["pricing"]["model"]
        if eur == 0:
            cost = "free audit" if model == "free-audit" else "free"
        else:
            cost = eur if eur in MISSING else f"EUR {eur:,.0f}"
        print(f"{r['suitability']['score']:>3}  {r['id']:<48} {cost:<14} {r['level']:<28} {r['title']}")
    print(f"\n{len(rows)} match(es)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
