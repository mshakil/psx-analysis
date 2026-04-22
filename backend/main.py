import asyncio
import os
import time
from contextlib import asynccontextmanager
from datetime import datetime

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from models import AnalysisRequest, AnalysisResponse, SignalsResponse, NewsData, FinancialsData
from scraper.price import load_symbol_cache, fetch_price_data, validate_ticker
from scraper.news import fetch_news
from scraper.financials import fetch_financials
from scraper.signals import fetch_ohlcv_yfinance, build_signals, translate_signals_to_plain_english
from ai_engine import run_analysis

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-haiku-4-5-20251001")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")

http_client: httpx.AsyncClient = None
_signals_cache: dict[str, tuple[float, SignalsResponse]] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: load symbol cache. Shutdown: close HTTP client."""
    global http_client
    http_client = httpx.AsyncClient(
        headers={"User-Agent": "IntelliTrade/1.0"},
        follow_redirects=True,
    )
    await load_symbol_cache(http_client)
    yield
    await http_client.aclose()


app = FastAPI(title="Intelli-Trade API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "model": CLAUDE_MODEL}


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze(request: AnalysisRequest):
    ticker = request.ticker.upper().strip()

    # Validate ticker
    is_valid, company_name, sector = await validate_ticker(ticker)
    if not is_valid:
        raise HTTPException(status_code=404, detail=f"Ticker '{ticker}' not found on PSX")

    if not ANTHROPIC_API_KEY:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not configured")

    # Fetch all data in parallel
    market_task = fetch_price_data(ticker, http_client)
    news_task = fetch_news(ticker, company_name, http_client)
    financials_task = fetch_financials(ticker, http_client)

    results = await asyncio.gather(
        market_task, news_task, financials_task, return_exceptions=True
    )

    market_data, news_data, financials_data = results

    # Handle failures gracefully
    if isinstance(market_data, Exception):
        raise HTTPException(status_code=502, detail=f"Failed to fetch price data: {str(market_data)}")

    if isinstance(news_data, Exception):
        news_data = NewsData(company_headlines=[], macro_headlines=[], sentiment_hint="NEUTRAL")

    if isinstance(financials_data, Exception):
        financials_data = FinancialsData(data_available=False)

    # Run AI analysis
    try:
        response = await run_analysis(
            market=market_data,
            news=news_data,
            financials=financials_data,
            checklist=request.checklist,
            api_key=ANTHROPIC_API_KEY,
            model=CLAUDE_MODEL,
        )
    except ValueError as e:
        raise HTTPException(status_code=500, detail=f"AI parsing error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"AI service error: {str(e)}")

    return response


@app.get("/signals/{ticker}", response_model=SignalsResponse)
async def get_signals(ticker: str, timeframe: int = 30):
    """Fetch technical signals: OHLCV, badges, entry/exit levels. Cached for 1 hour."""
    ticker = ticker.upper().strip()

    # Validate ticker
    is_valid, company_name, sector = await validate_ticker(ticker)
    if not is_valid:
        raise HTTPException(status_code=404, detail=f"Ticker '{ticker}' not found on PSX")

    # Validate timeframe
    valid_timeframes = [30, 60, 90, 252]
    if timeframe not in valid_timeframes:
        raise HTTPException(status_code=400, detail=f"Timeframe must be one of {valid_timeframes}")

    # Check cache (TTL: 3600 seconds = 1 hour)
    cache_key = f"{ticker}_{timeframe}"
    if cache_key in _signals_cache:
        cached_time, cached_response = _signals_cache[cache_key]
        if time.time() - cached_time < 3600:
            return cached_response

    # Fetch OHLCV data from yfinance
    try:
        ohlcv = await fetch_ohlcv_yfinance(ticker)
        if not ohlcv:
            raise HTTPException(status_code=404, detail=f"No OHLCV data found for {ticker}")

        # Slice to requested timeframe
        if len(ohlcv) > timeframe:
            ohlcv = ohlcv[-timeframe:]

        # Get 52-week high/low and current volume
        highs = [bar.high for bar in ohlcv]
        lows = [bar.low for bar in ohlcv]
        volumes = [bar.volume for bar in ohlcv]
        current_price = ohlcv[-1].close
        current_volume = volumes[-1]
        week_52_high = max(highs)
        week_52_low = min(lows)

        # Build signals
        signals_dict = build_signals(ohlcv, current_volume, week_52_high, week_52_low)

        # Translate to plain English badges
        badges = translate_signals_to_plain_english(signals_dict)

        # Build response
        entry_exit = signals_dict["entry_exit"]
        response = SignalsResponse(
            ticker=ticker,
            timeframe_days=len(ohlcv),
            ohlcv=ohlcv,
            badges=badges,
            entry_exit=entry_exit,
            support_level=signals_dict["support_resistance"].get("support"),
            resistance_level=signals_dict["support_resistance"].get("resistance"),
            sma20=signals_dict["sma20"],
            sma60=signals_dict["sma60"],
            sma120=signals_dict["sma120"],
            disclaimer="Not financial advice. For educational purposes only.",
            cached_at=datetime.utcnow().isoformat(),
        )

        # Cache result
        _signals_cache[cache_key] = (time.time(), response)

        return response

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Signal calculation error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Signal service error: {str(e)}")
