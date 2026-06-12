"""FinBERT sentiment wrapper (ProsusAI/finbert, runs locally)."""

import logging
from typing import Literal

logger = logging.getLogger(__name__)

SentimentLabel = Literal["positive", "negative", "neutral"]


class FinBERTSentiment:
    """
    Lazy-loaded FinBERT classifier.
    Model is downloaded once and cached by HuggingFace.
    """

    _MODEL_NAME = "ProsusAI/finbert"

    def __init__(self) -> None:
        self._pipeline = None

    def _load(self) -> None:
        if self._pipeline is not None:
            return
        try:
            from transformers import pipeline
            logger.info("Loading FinBERT model (first run: may take a minute)…")
            self._pipeline = pipeline(
                "text-classification",
                model=self._MODEL_NAME,
                tokenizer=self._MODEL_NAME,
                top_k=None,   # return all three label scores
            )
            logger.info("FinBERT loaded.")
        except Exception as exc:
            logger.error("FinBERT load failed: %s", exc)
            raise

    def score_text(self, text: str) -> dict:
        """
        Score a single text snippet.
        Returns: {label: str, score: float, raw: [{label, score}, ...]}
          score is in [-1, +1]: positive maps to +score, negative to -score, neutral to 0
        """
        self._load()
        text = text[:512]  # FinBERT max sequence length
        try:
            results = self._pipeline(text)[0]  # list of {label, score}
        except Exception as exc:
            logger.warning("FinBERT inference failed: %s", exc)
            return {"label": "neutral", "score": 0.0, "raw": []}

        scores_by_label = {r["label"].lower(): r["score"] for r in results}
        pos = scores_by_label.get("positive", 0.0)
        neg = scores_by_label.get("negative", 0.0)
        neu = scores_by_label.get("neutral", 0.0)

        # Composite scalar in [-1, +1]
        composite = pos - neg

        best = max(scores_by_label, key=lambda k: scores_by_label[k])
        return {
            "label": best,
            "score": composite,
            "raw": results,
        }

    def aggregate(self, texts: list[str]) -> dict:
        """
        Score multiple texts and return aggregate result.
        Returns: {label, score, count, positive_pct, negative_pct, neutral_pct}
        """
        if not texts:
            return {
                "label": "neutral",
                "score": 0.0,
                "count": 0,
                "positive_pct": 0.0,
                "negative_pct": 0.0,
                "neutral_pct": 0.0,
            }

        self._load()
        scored = [self.score_text(t) for t in texts]
        composite_mean = sum(s["score"] for s in scored) / len(scored)

        labels = [s["label"] for s in scored]
        n = len(labels)
        pos_pct = labels.count("positive") / n
        neg_pct = labels.count("negative") / n
        neu_pct = labels.count("neutral") / n

        if composite_mean >= 0.05:
            agg_label: SentimentLabel = "positive"
        elif composite_mean <= -0.05:
            agg_label = "negative"
        else:
            agg_label = "neutral"

        return {
            "label":        agg_label,
            "score":        composite_mean,
            "count":        n,
            "positive_pct": pos_pct,
            "negative_pct": neg_pct,
            "neutral_pct":  neu_pct,
        }


# Module-level singleton (lazily loaded on first use)
_SENTIMENT = FinBERTSentiment()


def score_instrument_sentiment(instrument: str) -> dict:
    """
    Fetch recent news for *instrument* and return aggregate sentiment.
    Requires data.news_feed to be importable.
    """
    from data.news_feed import get_news_texts
    texts = get_news_texts(instrument)
    result = _SENTIMENT.aggregate(texts)
    logger.info(
        "Sentiment [%s]: label=%s score=%.3f n=%d",
        instrument,
        result["label"],
        result["score"],
        result["count"],
    )
    return result
