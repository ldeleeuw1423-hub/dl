def combine_sentiment(
    news: float,
    reddit: float,
    fear_greed: int,
) -> float:
    """
    Combineert drie sentimentbronnen tot één score -1..+1.
    Gewichten: CryptoPanic 40%, Reddit 30%, Fear&Greed 30%.
    """
    fg_score = (fear_greed - 50) / 50   # 0-100 → -1..+1
    return news * 0.40 + reddit * 0.30 + fg_score * 0.30
