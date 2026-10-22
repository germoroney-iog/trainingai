"""Shared helpers for the training database scripts."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "trainings.json"
PATH_PATH = ROOT / "data" / "learning_path.json"
SCHEMA_PATH = ROOT / "schema" / "training.schema.json"
CATALOGUE_DIR = ROOT / "catalogue"

MISSING = ("not published", "not verified", "not applicable")

WEIGHTS = {
    "relevance": 0.30,
    "curriculum": 0.20,
    "practical": 0.20,
    "quality": 0.15,
    "value": 0.10,
    "accessibility": 0.05,
}

HIGHLY_RATED_MIN_RATIO = 0.9  # 4.5 on a 5-point scale
HIGHLY_RATED_MIN_COUNT = 100

CATEGORY_LABELS = {
    "strategy-operating-models": "AI strategy, operating models & ROI",
    "governance-regulation-risk": "Governance, regulation, responsible AI & risk",
    "security": "AI security",
    "generative-ai-agents": "Generative AI, LLMs, prompting & agents",
    "python-data": "Python & data analysis",
    "machine-learning-deep-learning": "Machine learning & deep learning",
    "rag-evals-llmops": "RAG, evaluation, deployment, MLOps & LLMOps",
    "cloud-platforms": "Cloud AI platforms & certifications",
    "sales-marketing-partnerships": "AI in sales, marketing & partnerships",
}

FREE_MODELS = ("free", "free-audit", "publicly-funded")


def load_json(path: Path):
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def dump_json(path: Path, data) -> None:
    text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    path.write_text(text, encoding="utf-8")


def weighted_score(components: dict) -> int:
    total = sum(components[k] * w for k, w in WEIGHTS.items())
    # Round half up so results do not depend on banker's rounding.
    return int(total + 0.5)


def expected_rating_class(rating: dict) -> str | None:
    """Return the rating class implied by a learner_rating block.

    Returns None when no rating is published; the record must then be
    "credible-but-unrated" and justify itself through quality_evidence.
    """
    if rating.get("status") != "published":
        return None
    ratio = rating["value"] / rating["scale"]
    if rating["review_count"] < HIGHLY_RATED_MIN_COUNT:
        return "rated-small-sample"
    if ratio >= HIGHLY_RATED_MIN_RATIO:
        return "highly-rated"
    return "rated-below-threshold"


def eur_for(pricing: dict, fx: dict):
    """Approximate EUR cost of the headline price, or a missing-value state."""
    amount, currency = pricing["amount"], pricing["currency"]
    if amount in MISSING:
        return amount
    if amount == 0:
        return 0
    if currency in MISSING:
        return "not verified"
    if currency == "EUR":
        return amount
    rate = fx["rates"].get(currency)
    if rate is None:
        return "not verified"
    return round(amount / rate, 2)


def norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def norm_url(url: str) -> str:
    url = url.strip().lower()
    url = re.sub(r"^https?://(www\.)?", "", url)
    url = url.split("?")[0].split("#")[0]
    return url.rstrip("/")
