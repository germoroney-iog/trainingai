# Instructions for AI agents maintaining this repository

- `data/` is authoritative; `catalogue/` is generated. Never edit `catalogue/` by hand. Run `scripts/build_catalogue.py`.
- Never invent courses, ratings, prices, accreditation, dates or outcomes. Use `not published`, `not verified` or `not applicable`.
- Never overwrite a record's `user` block, change an `id`, or delete a record. Use `scripts/upsert.py`, which matches on id, URL, then provider and title, and use `--archive` for withdrawn offerings.
- Ratings must be course-specific, with platform, scale, count, source URL and date. Apply the thresholds in `docs/SCORING.md`.
- Keep the suitability score separate from learner ratings. Recompute it from the weighted components.
- Before finishing, run `python scripts/validate.py --check-generated`. It must report 0 errors.
- Record each refresh in `docs/research/YYYY-MM-DD.md`.
- Full workflow: see README.md, "Maintaining and refreshing".
