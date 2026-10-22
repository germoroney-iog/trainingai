# trainingai

A maintained, source-backed database of free and paid AI training. It is curated for an experienced senior executive in
Ireland who is building capability in enterprise AI transformation, AI strategy and advisory work, board-level governance
and assurance, and practical AI engineering.

Every record links to its sources, says what could not be verified, and keeps the maintainer's suitability score
separate from published learner ratings. Nothing is guessed: missing facts are marked `not published` or `not verified`.

## Start here

| I want to… | Open |
|---|---|
| Browse everything, by subject or by score | [catalogue/CATALOGUE.md](catalogue/CATALOGUE.md) |
| See the best options quickly | [catalogue/SHORTLISTS.md](catalogue/SHORTLISTS.md): best free, best-value paid, executive and governance, practical technical |
| Follow a plan | [catalogue/LEARNING_PATH.md](catalogue/LEARNING_PATH.md): sequenced steps with prerequisites, hours and costs |
| Filter in a spreadsheet | [catalogue/trainings.csv](catalogue/trainings.csv) |
| Understand the scores and rating labels | [docs/SCORING.md](docs/SCORING.md) |
| Understand the fields | [docs/SCHEMA.md](docs/SCHEMA.md) |
| See what changed in a refresh and what is unverified | [docs/research/](docs/research/) |

## Layout

```
data/trainings.json         authoritative database (records + FX table)       ← edit
data/learning_path.json     suggested sequence (record ids + reasons)          ← edit
data/excluded.json          offerings reviewed and deliberately left out       ← edit
schema/training.schema.json JSON Schema for trainings.json
scripts/                    validate, search, upsert/archive, FX, build views
catalogue/                  GENERATED Markdown and CSV views                   ← never edit by hand
docs/                       schema guide, scoring method, dated research summaries
```

## Setup

Python 3.10 or later.

```bash
pip install -r requirements.txt     # jsonschema
python scripts/validate.py --check-generated
```

## Searching

```bash
python scripts/search.py governance                                  # free-text search
python scripts/search.py --category rag-evals-llmops --free          # free RAG / LLMOps training
python scripts/search.py --level advanced --max-eur 1000 --min-score 70
python scripts/search.py --credential professional-certification --sort cost
python scripts/search.py --highly-rated
python scripts/search.py --status planned                            # your own plan
```

The categories are `strategy-operating-models`, `governance-regulation-risk`, `security`, `generative-ai-agents`,
`python-data`, `machine-learning-deep-learning`, `rag-evals-llmops`, `cloud-platforms` and
`sales-marketing-partnerships`.

## Tracking your own progress

Each record has a `user` block that automated refreshes never overwrite:

```json
"user": { "completion_status": "in-progress", "notes": "Employer funding approved", "started_on": "2026-11-01" }
```

`completion_status` is one of `not-started`, `interested`, `planned`, `in-progress`, `completed` or `dropped`. Edit it
in `data/trainings.json`, then rebuild the views (see below).

## Maintaining and refreshing

Run this after any change:

```bash
python scripts/apply_fx.py          # only if prices or the fx table changed
python scripts/build_catalogue.py
python scripts/validate.py --check-generated
```

CI (`.github/workflows/validate.yml`) runs the last command on every push and pull request.

### Refreshing records (every 6 months or so; the validator warns after 180 days)

1. **Re-check existing records first.** For each one, open the official page and the rating source in `sources`.
   Confirm the price, curriculum, dates, credential, rating and availability.
2. **Write refreshed or new records** to a candidates file, `{"records": [ ... ]}`, using the schema. Use official
   pages for course facts and course-specific review pages for ratings. Never use a provider-wide rating.
3. **Merge:**

   ```bash
   python scripts/upsert.py candidates.json --dry-run    # preview
   python scripts/upsert.py candidates.json
   ```

   Candidates are matched by id, then official URL, then provider and title, so duplicates are not created. A match
   keeps its id, `user` block and history. Material changes (price, rating, status, credential, dates, title, URL,
   score) are appended to `history` automatically.
4. **Archive** withdrawn or superseded offerings. Never delete them:

   ```bash
   python scripts/upsert.py --archive old-id --reason "Exam retired 2027-01-14" --superseded-by new-id
   ```

5. **Update FX** if needed. Edit `fx` in `data/trainings.json` with the source, URL, rate date and rates
   (foreign units per EUR, for example from the ECB reference rates), then run `apply_fx.py`.
6. **Rebuild and validate** using the commands above.
7. **Write a dated summary** in `docs/research/YYYY-MM-DD.md` covering additions, changes, archived records,
   inaccessible sources, conflicting evidence and remaining gaps.

### Rules for adding a record

- Every record needs at least one source URL, preferably the official page plus the rating page.
- "Highly rated" means at least 4.5/5 (or 90% of scale) from at least 100 course-specific reviews. The validator
  enforces this.
- Programmes without public ratings may be added as "credible but unrated" only if `quality_evidence` explains the
  institutional, curriculum or assessment evidence.
- Keep assessed qualifications and certifications (`assessed-academic-qualification`, `professional-certification`,
  `assessed-completion-certificate`) distinct from completion and attendance certificates.
- Exclude promotional webinars, materially outdated courses and unsupported accreditation claims. Record them in
  `data/excluded.json` with the reason.
- Score suitability with the weights in [docs/SCORING.md](docs/SCORING.md). The validator recomputes the total.

## Caveats

- Prices and dates change often. Confirm them on the official page before enrolling. EUR figures are approximate and
  exclude VAT unless stated.
- Ratings from different platforms are not directly comparable.
- No course or credential here guarantees employment or advancement.
