import httpx
from bs4 import BeautifulSoup
from models import FinancialsData
import re

PSX_COMPANY_BASE = "https://dps.psx.com.pk/company"


def _safe_float(text: str) -> float | None:
    """Safely extract float from messy text."""
    if not text:
        return None
    cleaned = re.sub(r"[^\d.]", "", text.strip())
    try:
        return float(cleaned) if cleaned else None
    except ValueError:
        return None


async def fetch_financials(ticker: str, client: httpx.AsyncClient) -> FinancialsData:
    """
    Scrape PSX company page for PE, dividend yield, market cap.
    Returns data_available=False on any failure (graceful degradation).
    """
    url = f"{PSX_COMPANY_BASE}/{ticker.upper()}"
    try:
        resp = await client.get(url, timeout=10.0, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code != 200:
            return FinancialsData(data_available=False)

        soup = BeautifulSoup(resp.text, "lxml")

        def find_stat(label_text: str) -> str | None:
            """Find value by matching label text."""
            for tag in soup.find_all(string=re.compile(label_text, re.I)):
                parent = tag.parent
                if parent:
                    value_tag = parent.find_next_sibling()
                    if value_tag:
                        return value_tag.get_text(strip=True)
            return None

        pe = _safe_float(find_stat(r"P/E") or "")
        div_yield = _safe_float(find_stat(r"Yield") or "")
        mcap_raw = find_stat(r"Market Cap") or ""
        mcap_bn = None
        if mcap_raw:
            mcap_val = _safe_float(mcap_raw)
            if mcap_val:
                mcap_bn = mcap_val / 1e9 if mcap_val > 1e6 else mcap_val

        return FinancialsData(
            pe_ratio=pe,
            dividend_yield=div_yield,
            market_cap_bn_pkr=mcap_bn,
            data_available=(pe is not None or div_yield is not None),
        )
    except Exception:
        return FinancialsData(data_available=False)
