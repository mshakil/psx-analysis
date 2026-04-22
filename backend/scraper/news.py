import asyncio
import httpx
import feedparser
from models import NewsData

NEWS_BASE = "https://news.google.com/rss/search"

POSITIVE_KEYWORDS = {"profit", "record", "growth", "expansion", "dividend", "strong", "surge", "beat", "upgrade"}
NEGATIVE_KEYWORDS = {"loss", "debt", "decline", "default", "cut", "investigation", "lawsuit", "downgrade", "fall", "crash"}


def _classify_sentiment(headlines: list[str]) -> str:
    """Classify sentiment from headline keywords."""
    pos = sum(1 for h in headlines if any(w in h.lower() for w in POSITIVE_KEYWORDS))
    neg = sum(1 for h in headlines if any(w in h.lower() for w in NEGATIVE_KEYWORDS))
    if pos > neg + 1:
        return "POSITIVE"
    if neg > pos + 1:
        return "NEGATIVE"
    if pos > 0 and neg > 0:
        return "MIXED"
    return "NEUTRAL"


async def fetch_news(ticker: str, company_name: str, client: httpx.AsyncClient) -> NewsData:
    """
    Fetch company-specific and macro news from Google News RSS concurrently.
    """
    company_url = f"{NEWS_BASE}?q={ticker}+Pakistan+PSX&hl=en-PK&gl=PK&ceid=PK:en"
    macro_url = f"{NEWS_BASE}?q=Pakistan+economy+KSE100+rupee&hl=en-PK&gl=PK&ceid=PK:en"

    try:
        company_resp, macro_resp = await asyncio.gather(
            client.get(company_url, timeout=10.0),
            client.get(macro_url, timeout=10.0),
            return_exceptions=True
        )

        company_headlines = []
        if not isinstance(company_resp, Exception) and company_resp.status_code == 200:
            feed = feedparser.parse(company_resp.text)
            company_headlines = [e.title for e in feed.entries[:7]]

        macro_headlines = []
        if not isinstance(macro_resp, Exception) and macro_resp.status_code == 200:
            feed = feedparser.parse(macro_resp.text)
            macro_headlines = [e.title for e in feed.entries[:5]]

    except Exception:
        company_headlines = []
        macro_headlines = []

    sentiment = _classify_sentiment(company_headlines + macro_headlines)

    return NewsData(
        company_headlines=company_headlines,
        macro_headlines=macro_headlines,
        sentiment_hint=sentiment,
    )
