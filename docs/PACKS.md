# Use-case training packs

A pack answers the question "what training do I need to do *this*?" for one concrete use case. It is stored as
`data/packs/<id>.json` (schema: `schema/pack.schema.json`) and rendered to `catalogue/packs/<id>.md`.

A pack never copies course facts. It refers to records in `data/trainings.json` by `id`, so prices, hours, ratings and
availability stay in one place and every pack updates when the database is refreshed.

## Structure

| Field | Meaning |
|---|---|
| `id` | Stable slug, the same as the file name. |
| `title`, `use_case`, `outcome` | The use case in your own words, and what you will be able to do at the end. |
| `assumptions` | Starting point, such as existing skills, tools or constraints. |
| `capabilities[]` | The skills the use case needs, in learning order. Each has a `name`, a `why`, and `steps`. |
| `capabilities[].steps[]` | `{id, why, optional?, extra_costs?}`. `id` must be a record in `data/trainings.json`. `extra_costs` adds required costs sold separately, such as exam fees, to the totals. |
| `capabilities[].gap` | What no verified course covers yet. It is required when `steps` is empty, and allowed alongside steps for partial coverage. |
| `milestones[]` | Practical build steps: `{name, after_capabilities: [capability numbers], deliverable}`. |
| `research_queue[]` | Topics to research to close gaps. The weekly refresh works through these. |
| `notes[]`, `history[]` | Free notes, and a dated change log. Add an entry and bump `updated_on` whenever you change the pack. |

## Adding a new pack

1. Describe the use case in one sentence and list the capabilities it needs. Think in terms of "to do this I must be
   able to…".
2. Search the database for each capability: `python scripts/search.py <words>` or `--category …`.
3. Where nothing suitable exists, research new offerings using the rules in `README.md` and add them with
   `scripts/upsert.py`. If none can be verified, record a `gap` and add the topic to `research_queue`. Never point a
   step at an unverified course.
4. Add milestones that turn the training into something you build or deliver.
5. Run `python scripts/build_catalogue.py` and `python scripts/validate.py --check-generated`.

## Expanding an existing pack

- Add steps as new records arrive, and mark one-off alternatives `optional`.
- Remove a `gap` only when a verified record covers it.
- If a referenced record is archived, the validator warns. Replace the step with the record named in its
  `superseded_by` field, or another suitable one.
