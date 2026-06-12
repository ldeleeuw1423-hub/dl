"""
Quick smoke-test for the FinBERT sentiment module.
Tests with hard-coded headlines (no Finnhub API key needed).

Run: python run_sentiment_test.py
"""

from ai.sentiment import FinBERTSentiment

HEADLINES = [
    "EUR/USD surges to 3-month high after strong eurozone GDP data",
    "Federal Reserve signals aggressive rate hikes amid persistent inflation",
    "EUR/USD range-bound as traders await central bank guidance",
    "Recession fears mount as German manufacturing PMI hits 2-year low",
    "Dollar strengthens on robust US jobs report beating all forecasts",
]


def main() -> None:
    model = FinBERTSentiment()
    print("\n=== FinBERT Sentiment Test ===\n")
    for headline in HEADLINES:
        result = model.score_text(headline)
        bar = "█" * int(abs(result["score"]) * 20)
        sign = "+" if result["score"] >= 0 else ""
        print(f"  {result['label']:>10}  {sign}{result['score']:.3f}  {bar}")
        print(f"  '{headline[:70]}'\n")

    agg = model.aggregate(HEADLINES)
    print(f"Aggregate: label={agg['label']}  score={agg['score']:.3f}  n={agg['count']}")
    print(
        f"           pos={agg['positive_pct']*100:.0f}%  "
        f"neg={agg['negative_pct']*100:.0f}%  "
        f"neu={agg['neutral_pct']*100:.0f}%"
    )


if __name__ == "__main__":
    main()
