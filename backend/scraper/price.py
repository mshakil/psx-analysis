import httpx
import datetime
from models import MarketData

PSX_EOD_BASE = "https://dps.psx.com.pk/timeseries/eod"
PSX_SYMBOLS_URL = "https://dps.psx.com.pk/symbols"

_SYMBOL_CACHE: dict[str, dict] = {}


async def load_symbol_cache(client: httpx.AsyncClient) -> None:
    """Load symbol cache at FastAPI startup."""
    resp = await client.get(PSX_SYMBOLS_URL, timeout=15.0)
    resp.raise_for_status()
    symbols = resp.json()
    for s in symbols:
        if not s.get("isDebt") and not s.get("isETF"):
            _SYMBOL_CACHE[s["symbol"]] = s
    print(f"Loaded {len(_SYMBOL_CACHE)} PSX symbols to cache")


async def validate_ticker(ticker: str) -> tuple[bool, str, str]:
    """Validate ticker and return (is_valid, company_name, sector_name)."""
    sym = _SYMBOL_CACHE.get(ticker.upper())
    if not sym:
        return False, "", ""
    return True, sym.get("name", ticker), sym.get("sectorName", "UNKNOWN")


async def fetch_price_data(ticker: str, client: httpx.AsyncClient) -> MarketData:
    """
    Fetch 252 trading days (~1 year) of EOD data from PSX.
    Compute all derived fields: trend, 52-week hi/lo, avg volume.
    """
    url = f"{PSX_EOD_BASE}/{ticker.upper()}?length=252"
    resp = await client.get(url, timeout=15.0)
    resp.raise_for_status()
    raw = resp.json()

    if raw.get("status") != 1 or not raw.get("data"):
        raise ValueError(f"No EOD data for {ticker}")

    rows = raw["data"]
    recent = rows[:252]

    # Current snapshot (index 0 = most recent/today)
    today = recent[0]
    yesterday = recent[1] if len(recent) > 1 else today

    current_price = today[1]  # close
    current_volume = today[2]  # volume
    open_price = today[3]  # open
    prev_close = yesterday[1]

    price_change_pct = round(((current_price - prev_close) / prev_close) * 100, 2)

    # 30-day average volume
    vols_30d = [r[2] for r in recent[:30]]
    avg_volume_30d = sum(vols_30d) / len(vols_30d)

    # 52-week high/low
    closes = [r[1] for r in recent]
    week_52_high = max(closes)
    week_52_low = min(closes)
    price_vs_52w_high_pct = round(((current_price - week_52_high) / week_52_high) * 100, 2)

    # Trend: compare 20-day vs 60-day moving average
    avg_20 = sum(closes[:20]) / 20 if len(closes) >= 20 else current_price
    avg_60 = sum(closes[:60]) / 60 if len(closes) >= 60 else current_price
    if avg_20 > avg_60 * 1.02:
        trend = "UPTREND"
    elif avg_20 < avg_60 * 0.98:
        trend = "DOWNTREND"
    else:
        trend = "SIDEWAYS"

    # Last 30 days for charting (chronological order)
    def ts_to_date(ts: int) -> str:
        return datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d")

    recent_prices = [{"date": ts_to_date(r[0]), "close": r[1], "volume": r[2]} for r in recent[:30]]
    recent_prices.reverse()

    sym_info = _SYMBOL_CACHE.get(ticker.upper(), {})
    return MarketData(
        ticker=ticker.upper(),
        company_name=sym_info.get("name", ticker),
        sector=sym_info.get("sectorName", "UNKNOWN"),
        current_price=current_price,
        open_price=open_price,
        price_change_pct=price_change_pct,
        avg_volume_30d=round(avg_volume_30d),
        current_volume=current_volume,
        week_52_high=week_52_high,
        week_52_low=week_52_low,
        price_vs_52w_high_pct=price_vs_52w_high_pct,
        trend_direction=trend,
        recent_prices=recent_prices,
    )
