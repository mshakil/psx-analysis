import asyncio
import os
import time
from contextlib import asynccontextmanager
from datetime import datetime

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from models import (
    AnalysisRequest, AnalysisResponse, SignalsResponse, NewsData, FinancialsData,
    FundAnalysisRequest, FundAnalysisResponse, FundListItem, FundSignalsResponse,
    FundComparisonResponse, FundComparisonSummary,
)
from scraper.price import load_symbol_cache, fetch_price_data, validate_ticker
from scraper.news import fetch_news
from scraper.financials import fetch_financials
from scraper.signals import fetch_ohlcv_psx, build_signals, translate_signals_to_plain_english
from scraper.mutual_funds import (
    load_fund_cache, validate_fund_code, search_funds,
    fetch_fund_info, fetch_fund_nav_history, fetch_fund_performance, fetch_fund_composition,
)
from ai_engine import run_analysis, run_fund_analysis

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-haiku-4-5-20251001")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")

http_client: httpx.AsyncClient = None
_signals_cache: dict[str, tuple[float, SignalsResponse]] = {}
_fund_analysis_cache: dict[str, tuple[float, FundAnalysisResponse]] = {}
_fund_signals_cache: dict[str, tuple[float, FundSignalsResponse]] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: load symbol cache + fund cache. Shutdown: close HTTP client."""
    global http_client
    http_client = httpx.AsyncClient(
        headers={"User-Agent": "IntelliTrade/1.0"},
        follow_redirects=True,
    )
    # Load both caches in parallel
    await asyncio.gather(load_symbol_cache(http_client), load_fund_cache(http_client))
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

    # Fetch OHLCV data from PSX EOD API
    try:
        ohlcv = await fetch_ohlcv_psx(ticker, http_client)
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


# ============================================
# PHASE 3: MUTUAL FUND ENDPOINTS
# ============================================

def build_fund_signals(nav_bars: list) -> dict:
    """
    Build fund signals from NAV history.
    Converts NAV bars to float list, reuses existing signal computation functions.
    Returns dict with badges, SMAs, trend_direction.
    """
    from scraper.signals import compute_moving_averages, compute_volatility, compute_trend_signal

    if len(nav_bars) < 20:
        return {
            "sma20": None,
            "sma60": None,
            "sma120": None,
            "trend_direction": "INSUFFICIENT_DATA",
            "volatility": "UNKNOWN",
        }

    closes = [bar.nav for bar in nav_bars]

    # Compute moving averages
    smas = compute_moving_averages(closes)

    # Compute volatility
    volatility_result = compute_volatility(closes)

    # Compute trend
    trend_result = compute_trend_signal(smas.get("sma20"), smas.get("sma60"), smas.get("sma120"), closes[-1])

    return {
        "sma20": smas.get("sma20"),
        "sma60": smas.get("sma60"),
        "sma120": smas.get("sma120"),
        "trend_direction": trend_result.get("direction", "SIDEWAYS"),
        "volatility": volatility_result.get("label", "MODERATE"),
    }


@app.get("/funds", response_model=list[FundListItem])
async def get_funds(type: str = None):
    """Get list of all MUFAP funds. Optional ?type= filter."""
    from scraper.mutual_funds import _FUND_CACHE

    if not _FUND_CACHE:
        raise HTTPException(status_code=503, detail="Fund cache not loaded yet")

    funds = list(_FUND_CACHE.values())

    # Filter by type if provided
    if type:
        type_upper = type.upper()
        funds = [f for f in funds if f.get("fund_type") == type_upper]

    return [FundListItem(**f) for f in funds]


@app.get("/funds/search", response_model=list[FundListItem])
async def search_funds_endpoint(q: str):
    """Search funds by code or name (in-memory, instant)."""
    if len(q) < 2:
        raise HTTPException(status_code=400, detail="Query must be at least 2 characters")

    results = search_funds(q, limit=20)
    return [FundListItem(**f) for f in results]


@app.post("/analyze/fund", response_model=FundAnalysisResponse)
async def analyze_fund(request: FundAnalysisRequest):
    """Full AI analysis for a mutual fund. ~12-18 seconds."""
    fund_code = request.fund_code.upper().strip()

    # Validate fund
    is_valid, fund_name, fund_type = validate_fund_code(fund_code)
    if not is_valid:
        raise HTTPException(status_code=404, detail=f"Fund '{fund_code}' not found on MUFAP")

    if not ANTHROPIC_API_KEY:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not configured")

    # Check cache (1-hour TTL)
    cache_key = fund_code
    if cache_key in _fund_analysis_cache:
        cached_time, cached_response = _fund_analysis_cache[cache_key]
        if time.time() - cached_time < 3600:
            return cached_response

    # Fetch all fund data in parallel
    fund_info_task = fetch_fund_info(fund_code, http_client)
    nav_history_task = fetch_fund_nav_history(fund_code, http_client)
    performance_task = fetch_fund_performance(fund_code, http_client)
    composition_task = fetch_fund_composition(fund_code, http_client)

    results = await asyncio.gather(
        fund_info_task, nav_history_task, performance_task, composition_task,
        return_exceptions=True
    )

    fund_info, nav_history, performance, composition = results

    # Handle failures gracefully (soft-fail pattern)
    if isinstance(fund_info, Exception):
        fund_info = FundInfoData(fund_code=fund_code, fund_name=fund_name, fund_type=fund_type, amc_name="", data_available=False)

    if isinstance(nav_history, Exception):
        nav_history = FundNavHistory(fund_code=fund_code, nav_bars=[], data_available=False)

    if isinstance(performance, Exception):
        performance = FundPerformanceData(data_available=False)

    if isinstance(composition, Exception):
        composition = FundCompositionData(data_available=False)

    # Run AI analysis
    try:
        response = await run_fund_analysis(
            fund_info=fund_info,
            nav_history=nav_history,
            performance=performance,
            composition=composition,
            checklist=request.checklist,
            api_key=ANTHROPIC_API_KEY,
            model=CLAUDE_MODEL,
        )
    except ValueError as e:
        raise HTTPException(status_code=500, detail=f"AI parsing error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"AI service error: {str(e)}")

    # Cache result
    _fund_analysis_cache[cache_key] = (time.time(), response)

    return response


@app.get("/signals/fund/{fund_code}", response_model=FundSignalsResponse)
async def get_fund_signals(fund_code: str, timeframe: int = 252):
    """Fund signals: NAV history + technical signals. ~3-5 seconds. 1-hour cache."""
    fund_code = fund_code.upper().strip()

    # Validate fund
    is_valid, fund_name, fund_type = validate_fund_code(fund_code)
    if not is_valid:
        raise HTTPException(status_code=404, detail=f"Fund '{fund_code}' not found on MUFAP")

    # Validate timeframe
    valid_timeframes = [30, 60, 90, 252, 1000]
    if timeframe not in valid_timeframes:
        raise HTTPException(status_code=400, detail=f"Timeframe must be one of {valid_timeframes}")

    # Check cache (1-hour TTL)
    cache_key = f"{fund_code}_{timeframe}"
    if cache_key in _fund_signals_cache:
        cached_time, cached_response = _fund_signals_cache[cache_key]
        if time.time() - cached_time < 3600:
            return cached_response

    # Fetch NAV history
    try:
        nav_history = await fetch_fund_nav_history(fund_code, http_client, length=1000)
        if not nav_history.data_available or not nav_history.nav_bars:
            raise HTTPException(status_code=404, detail=f"No NAV data found for {fund_code}")

        # Slice to requested timeframe
        nav_bars = nav_history.nav_bars
        if len(nav_bars) > timeframe:
            nav_bars = nav_bars[-timeframe:]

        # Build signals
        signals_dict = build_fund_signals(nav_bars)

        # Build response (fund signals use same SignalBadge structure)
        from scraper.signals import translate_signals_to_plain_english
        badges = translate_signals_to_plain_english(signals_dict) if signals_dict else []

        response = FundSignalsResponse(
            fund_code=fund_code,
            timeframe_days=len(nav_bars),
            nav_history=nav_bars,
            badges=badges,
            trend_direction=signals_dict.get("trend_direction", "SIDEWAYS"),
            sma20=signals_dict.get("sma20"),
            sma60=signals_dict.get("sma60"),
            sma120=signals_dict.get("sma120"),
            disclaimer="Not financial advice. For educational purposes only.",
            cached_at=datetime.utcnow().isoformat(),
        )

        # Cache result
        _fund_signals_cache[cache_key] = (time.time(), response)

        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Fund signals error: {str(e)}")


@app.get("/compare/funds", response_model=FundComparisonResponse)
async def compare_funds(codes: str):
    """Compare 2-3 funds side-by-side using cached analysis data."""
    # Parse and validate codes
    code_list = [c.strip().upper() for c in codes.split(",") if c.strip()]

    if len(code_list) < 2 or len(code_list) > 3:
        raise HTTPException(status_code=400, detail="Must provide 2-3 fund codes (comma-separated)")

    # Validate all funds exist
    for code in code_list:
        is_valid, _, _ = validate_fund_code(code)
        if not is_valid:
            raise HTTPException(status_code=404, detail=f"Fund '{code}' not found on MUFAP")

    if not ANTHROPIC_API_KEY:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not configured")

    # Fetch/use cached analyses for each fund
    fund_analyses = []
    for code in code_list:
        # Check cache first
        if code in _fund_analysis_cache:
            cached_time, cached_response = _fund_analysis_cache[code]
            if time.time() - cached_time < 3600:
                fund_analyses.append(cached_response)
                continue

        # Fetch fresh if not cached
        fund_info = await fetch_fund_info(code, http_client)
        nav_history = await fetch_fund_nav_history(code, http_client)
        performance = await fetch_fund_performance(code, http_client)
        composition = await fetch_fund_composition(code, http_client)

        # Soft-fail fallbacks
        if isinstance(fund_info, Exception):
            fund_info = FundInfoData(fund_code=code, fund_name="", fund_type="", amc_name="", data_available=False)
        if isinstance(nav_history, Exception):
            nav_history = FundNavHistory(fund_code=code, nav_bars=[], data_available=False)
        if isinstance(performance, Exception):
            performance = FundPerformanceData(data_available=False)
        if isinstance(composition, Exception):
            composition = FundCompositionData(data_available=False)

        try:
            response = await run_fund_analysis(
                fund_info=fund_info,
                nav_history=nav_history,
                performance=performance,
                composition=composition,
                checklist=None,
                api_key=ANTHROPIC_API_KEY,
                model=CLAUDE_MODEL,
            )
            fund_analyses.append(response)
            _fund_analysis_cache[code] = (time.time(), response)
        except Exception:
            raise HTTPException(status_code=503, detail=f"Failed to analyze fund {code}")

    # Build comparison summary
    returns_1y = [f.performance_metrics.returns_1y for f in fund_analyses if f.performance_metrics.returns_1y]
    total_costs = [f.fee_structure.total_cost for f in fund_analyses if f.fee_structure.total_cost]
    sharpe_ratios = [f.performance_metrics.sharpe_ratio for f in fund_analyses if f.performance_metrics.sharpe_ratio]
    verdict_ranks = {"BUY NOW": 5, "BUY SLOWLY": 4, "HOLD": 3, "STAY AWAY": 2, "SELL": 1}

    better_returns = None
    if returns_1y:
        idx = max(range(len(fund_analyses)), key=lambda i: fund_analyses[i].performance_metrics.returns_1y or -999)
        better_returns = fund_analyses[idx].fund_name

    lower_fees = None
    if total_costs:
        idx = min(range(len(fund_analyses)), key=lambda i: fund_analyses[i].fee_structure.total_cost or 999)
        lower_fees = fund_analyses[idx].fund_name

    best_risk_adjusted = None
    if sharpe_ratios:
        idx = max(range(len(fund_analyses)), key=lambda i: fund_analyses[i].performance_metrics.sharpe_ratio or -999)
        best_risk_adjusted = fund_analyses[idx].fund_name

    overall_winner = max(
        fund_analyses,
        key=lambda f: verdict_ranks.get(f.verdict, 0)
    ).fund_name

    return FundComparisonResponse(
        funds=fund_analyses,
        comparison=FundComparisonSummary(
            better_returns=better_returns,
            lower_fees=lower_fees,
            best_risk_adjusted=best_risk_adjusted,
            overall_winner=overall_winner,
        ),
    )
