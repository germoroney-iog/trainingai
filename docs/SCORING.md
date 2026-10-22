# Suitability scoring and rating rules

Two separate measures are recorded for every offering. Neither is a guarantee of quality, recognition or employment.

1. **Learner rating**: what learners say, copied exactly from a course-specific review source.
2. **Suitability score**: the maintainer's own judgement of fit for the learner profile below.

## Learner profile the score is calibrated for

An experienced senior executive based in Ireland who wants to strengthen opportunities in:

- enterprise AI transformation and adoption;
- AI strategy, commercial leadership and advisory work;
- board governance, responsible AI, risk and assurance;
- practical AI engineering and implementation.

Remote delivery that works from Ireland (GMT/IST) is preferred.

## Learner ratings

- Only course- or programme-specific ratings are recorded. A provider's overall rating (for example a platform's
  Trustpilot score) is never used.
- Each published rating records platform, value, scale, count, whether the count is reviews or star ratings, the
  scope (for example "aggregate of the courses in this specialization"), the source URL and the verification date.
- **Highly rated** means at least 4.5/5, or an equivalent 90% of scale, from at least 100 course-specific reviews or ratings.
- **Rated (small sample)** means a published rating from fewer than 100 reviews. Treat it as weak evidence.
- **Rated (below 4.5/5)** means at least 100 reviews but below the 90% threshold.
- **Credible but unrated** means no public course-specific rating. The record must say what supports its inclusion
  instead: institutional standing, assessed or proctored examination, accreditation or credit, or a current,
  detailed curriculum.
- Ratings from different platforms use different populations and prompts, so **they are not directly comparable**.
  A 4.8 on Coursera and a 4.8 on Maven are not equivalent evidence.

`scripts/validate.py` enforces these classes from the stored numbers.

## Suitability score (0–100)

Each component is scored 0–100, then weighted:

| Component | Weight | What earns a high score |
|---|---:|---|
| Relevance to the objectives above | 30% | Directly builds transformation, strategy, governance or implementation capability at a senior level |
| Curriculum depth and currency | 20% | Substantial, up-to-date syllabus (generative AI content revised 2024 or later; current regulation, including the EU AI Act) |
| Practical work and assessment | 20% | Graded projects, labs, capstones, proctored exams; not just videos and quizzes |
| Quality evidence and credential recognition | 15% | Strong learner ratings, institutional reputation, assessed or proctored credentials recognised by employers or regulators |
| Value for money | 10% | Benefit relative to cost and time, including exam, renewal and subscription costs |
| Remote accessibility and flexibility | 5% | Fully remote, self-paced or Irish-time-friendly live sessions, open to Irish residents |

`score = round(0.30·relevance + 0.20·curriculum + 0.20·practical + 0.15·quality + 0.10·value + 0.05·accessibility)`,
rounded half up. The validator recomputes it, so components and score cannot drift apart.

### Guard-rails

- Price is not treated as a sign of quality. An expensive programme scores well on value only when its depth,
  assessment and recognition justify the cost.
- Certificates are not treated as employment outcomes. Career claims made by providers are not recorded as evidence.
- Completion and attendance certificates score lower on quality and credential recognition than proctored certifications
  or credit-bearing university assessment.

### Confidence and missing evidence

`suitability.confidence` states how far the score rests on verified facts:

- **high**: official curriculum, assessment, price and (if any) rating verified.
- **medium**: core facts verified, but some of price, hours, dates or assessment detail are missing or came from
  secondary pages.
- **low**: significant facts unverified. Use the score only as a pointer to investigate.

Missing evidence is **never filled with a guess**. It lowers the relevant component (usually quality or value) and
the confidence level, and it appears in `verification.gaps`. Re-score the record once the gap is closed.
