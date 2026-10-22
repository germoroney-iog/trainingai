# Data model

Authoritative data lives in `data/`. Everything in `catalogue/` is generated from it.

| File | Role | Edited by |
|---|---|---|
| `data/trainings.json` | The training database (all records, plus the FX table) | People and `scripts/upsert.py` / `scripts/apply_fx.py` |
| `data/learning_path.json` | Suggested learning sequence (record IDs plus reasons) | People |
| `schema/training.schema.json` | JSON Schema (draft 2020-12) for `data/trainings.json` | People |
| `catalogue/*` | Markdown and CSV views | `scripts/build_catalogue.py` only |

## Missing values

Where a value cannot be confirmed, use one of these strings instead of guessing:

- `"not published"`: the provider does not publish it.
- `"not verified"`: it may be published, but the maintainer could not confirm it at the last check.
- `"not applicable"`: the field does not apply, for example an exam renewal on a course with no exam.

## Record fields

| Field | Meaning |
|---|---|
| `id` | Stable slug (`provider-short-title`). Never renamed or reused, including after archiving. |
| `title`, `provider`, `platform`, `official_url` | What it is, who teaches it, where it is delivered, the canonical official page. |
| `offering_type` | `university-programme`, `executive-education`, `professional-certification`, `specialization`, `course`, `short-course`, `workshop`, `learning-path`. |
| `categories` | One or more subject tags (see below). |
| `audience`, `level`, `prerequisites` | Who it is for, its difficulty, and stated prerequisites. An empty list means none are stated. |
| `learning_outcomes`, `practical_work` | What you learn, and the projects or labs. An empty `practical_work` list means none are advertised. |
| `assessment.type` / `.description` | How learning is assessed (`none`, `auto-graded-quizzes`, `graded-assignments`, `peer-reviewed`, `proctored-exam`, `capstone-project`, `academic-assessment`, `mixed`). |
| `credential.type` | Separates **assessed** credentials (`assessed-academic-qualification`, `professional-certification`, `assessed-completion-certificate`) from `completion-certificate`, `attendance-certificate`, `digital-badge` and `none`. |
| `credential.issuer`, `.academic_credit`, `.renewal` | Issuing body, ECTS or other credit, and renewal or continuing-education requirements. |
| `delivery` | Format, advertised duration, study hours (`min`, `max` and `basis`), access period, and start dates or on-demand availability. |
| `ireland_access` | Whether Irish residents can enrol, with notes and live-session time zones. |
| `pricing.model` | `free`, `free-audit`, `subscription`, `one-off`, `publicly-funded` (for example Springboard+), `mixed`. |
| `pricing.advertised`, `.amount`, `.currency` | The price as advertised, the headline number and its ISO currency. |
| `pricing.eur_approx` | **Generated** by `scripts/apply_fx.py` from the top-level `fx` table (source, URL and rate date are recorded there). |
| `pricing.additional_costs`, `.financial_aid` | Exam, certificate, subscription, cloud, VAT and renewal costs, and only those scholarships, aid or discounts that were verified. |
| `learner_rating` | `status` is `published`, `not published` or `not verified`. When published it also holds `platform`, `value`, `scale`, `review_count`, `count_type`, `scope`, `source_url` and `verified_on`. |
| `rating_class` | `highly-rated`, `rated-small-sample`, `rated-below-threshold` or `credible-but-unrated` (rules in [SCORING.md](SCORING.md)). |
| `quality_evidence`, `limitations`, `relevance` | Why it is included, its weaknesses, and how it serves the objectives. |
| `suitability` | Score, component scores, confidence and rationale ([SCORING.md](SCORING.md)). |
| `status` | `active`, `upcoming`, `paused`, `archived` or `not verified`. Archived records need an `archive` block (`date`, `reason`, optional `superseded_by`). |
| `sources` | Every supporting URL, the facts it supports, and when it was accessed. |
| `verification` | `last_verified`, `method`, `gaps` (unverified facts) and `conflicts` (sources that disagree). |
| `user` | **Yours.** `completion_status` (`not-started`, `interested`, `planned`, `in-progress`, `completed`, `dropped`), `notes`, and optional `started_on` and `completed_on`. Automated refreshes never overwrite it. |
| `history` | Dated log of material changes (price, rating, status, credential, dates, score). It is append-only. |

### Subject categories

`strategy-operating-models`, `governance-regulation-risk`, `security`, `generative-ai-agents`, `python-data`,
`machine-learning-deep-learning`, `rag-evals-llmops`, `cloud-platforms`, `sales-marketing-partnerships`.

## Validation

`scripts/validate.py` checks the JSON Schema and also checks:

- IDs are unique, with no two current records sharing an official URL or a provider and title;
- each `rating_class` is consistent with the stored rating;
- each `suitability.score` equals its weighted components;
- each `eur_approx` matches the FX table;
- dates are not in the future, and history is in date order;
- learning-path steps point at existing records;
- with `--check-generated`, `catalogue/` is up to date.

It warns, without failing, on records last verified more than 180 days ago.
