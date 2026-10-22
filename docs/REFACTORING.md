# Refactoring backlog

Audit of the repository on 2026-10-22 (57 records, 2 use-case packs). The code works and
`scripts/validate.py --check-generated` passes. The items below are improvements, ordered by value.
Line references are to the code as of this audit.

## High value

### 1. Unify the learning path with use-case packs

- `data/learning_path.json` (stages → steps) and `data/packs/*.json` (capabilities → steps) have the same step shape,
  extra costs and totals.
- Only packs have a JSON Schema. The learning path is checked by hand-written code in `scripts/validate.py` (about
  lines 103–119).
- The extra-cost check exists twice: inline in that learning-path block, and in `check_extra_costs`.

**Fix:** convert the learning path into a pack, for example `data/packs/executive-core-path.json`. Then delete the
special-case validation and `learning_path_md`.

### 2. Fix pricing fields that carry more than one meaning

- **`pricing.model: "mixed"` is used to mean "price unknown"** on 4 records:
  `deeplearningai-long-term-agentic-memory-langgraph`, `deeplearningai-red-teaming-llm-applications`,
  `google-skills-deploy-production-ready-agents` and `deeplearningai-evaluating-ai-agents`. That is misleading in
  search and shortlists. **Fix:** add an explicit `"not verified"` model value.
- **`pricing.amount` has no fixed meaning:** it can be a programme total (UCD, calculated), 0 for the audit route of
  a free-audit course whose certificate is paid, or unknown. **Fix:** add `amount_basis`, one of `total`, `per-year`,
  `per-month`, `per-attempt` or `audit-route`.
- **Extra costs are free text:** 22 `additional_costs` entries contain amounts as text. That is why packs restate
  the AIGP exam fee as `extra_costs`. **Fix:** store them as structured entries:
  `{description, amount, currency, required}`. Totals can then include required costs automatically, and
  pack-level `extra_costs` can be removed.

### 3. Add unit tests

CI only runs the validator. Add a pytest suite under `tests/`, run in `.github/workflows/validate.yml`, covering:

- `weighted_score` rounding (half up);
- the `expected_rating_class` thresholds (4.5/5 and 100 reviews, small samples, ratings below the threshold);
- `eur_for`, including missing values and currencies not in the FX table;
- `upsert.merge`: keeps `id`, `user` and `history`, and logs material changes;
- archiving with `--superseded-by`;
- pack validation: unknown id, id that doesn't match the file name, milestone pointing at a missing capability, and
  a capability with no steps and no gap.

### 4. Split `data/trainings.json` into one file per record

The file is about 7,600 lines and every weekly refresh pull request edits it, so concurrent refreshes will conflict
and diffs are hard to review. **Fix:** move to `data/records/<id>.json` plus `data/fx.json`. IDs already map 1:1 to
file names. Do this after the open pull request is merged and before weekly refresh pull requests accumulate.

## Code structure

### 5. Break up `scripts/build_catalogue.py` (about 500 lines)

- It mixes formatting helpers, five different views, CSV export, pack rendering and file writing.
- `record_detail` assembles Markdown by joining lines and then removing triple blank lines, which is fragile.

**Fix:** split it into `format.py` (money, hours, price, rating and credential labels), `views.py` and a thin
`build_catalogue.py`. Build each record detail from a list of blocks.

### 6. Remove duplicated logic

- **Duplicate detection:** URL and provider-plus-title matching appears in both `validate.py` and
  `upsert.find_match`. **Fix:** a single `match_keys(rec)` in `common.py`.
- **Cost display:** `search.py` has its own free/EUR formatting and repeats the free-pricing check (`is_free`).
  **Fix:** reuse the shared formatting helpers.
- **Shortlist categories:** the executive and technical category groups are hard-coded in `build_catalogue.py`.
  **Fix:** move them to `common.py` next to `CATEGORY_LABELS`.

### 7. Restructure `scripts/validate.py`

- `validate()` is one long loop. **Fix:** split it into small per-record check functions, which are easier to
  extend and to unit test.
- It imports `build_catalogue` inside `main()` to check whether the generated files are stale. **Fix:** move
  `render()` and `stale_outputs()` to a shared module.

### 8. Make `scripts/upsert.py` safer

- **No check before writing:** it writes candidates without validating them. **Fix:** validate the merged database
  in memory and refuse to write on errors.
- **No partial updates:** a refresh must supply the whole record. **Fix:** add a `--patch` mode for updating a few
  fields, such as price, dates or rating.
- **Unchecked archive link:** `--archive --superseded-by` does not check that the replacement ID exists. **Fix:**
  check it.
- **Packs left pointing at archived records:** archiving a record that a pack uses only produces a later validator
  warning. **Fix:** list the affected packs when archiving.

### 9. Turn the scripts into a package

The scripts import `common` by relying on the script's own folder being on Python's path. That blocks `python -m`
and clean test imports. **Fix:** move the code into a small `trainingai/` package with thin command-line entry
points.

## Smaller items

### 10. Keep a single source of truth for rules

- The scoring weights and thresholds appear in `common.py`, `docs/SCORING.md` and the weekly routine's prompt.
- The category list appears in the schema and in `CATEGORY_LABELS`. They match today, but nothing enforces it.

**Fix:** add a test that compares them, or generate the `docs/SCORING.md` table from `common.py`.

### 11. Split the big catalogue page

`catalogue/CATALOGUE.md` is about 260 KB, which is slow to open on GitHub. **Fix:** per-record pages under
`catalogue/records/`, with the summary and subject tables kept on one page.

### 12. Generator and validator tidy-ups

- `stale_outputs` renders every file twice.
- `render()` loads the packs itself when they are not passed in.
- `optional` and `extra_costs` are checked differently for packs and for the learning path. Item 1 resolves this.

## Suggested order

1. Tests (3), so later changes are safe.
2. Pricing model fixes (2). This is a data-quality issue the weekly refresh will repeat.
3. Unify the learning path with packs (1), and make upsert safer (8).
4. Structural splits (4, 5, 6, 7, 9).
5. The remaining items as time allows.
