import asyncio
import os
from contextlib import asynccontextmanager

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from models import AnalysisRequest, AnalysisResponse
from scraper.price import load_symbol_cache, fetch_price_data, validate_ticker
from scraper.news import fetch_news
from scraper.financials import fetch_financials
from ai_engine import run_analysis

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-haiku-4-5-20251001")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")

http_client: httpx.AsyncClient = None


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
