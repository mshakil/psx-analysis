# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Intelli-Trade** is an AI-powered financial decision engine for the Pakistan Stock Exchange (PSX).

**Architecture:**
- **Frontend:** React.js (displays verdict badge, summary, risk, confidence, chart)
- **Backend:** FastAPI (REST API consuming AI-generated JSON)
- **AI Layer:** LLM-powered analysis engine that synthesizes market data, news, and fundamentals into actionable verdicts

**Response SLA:** 15–20 seconds (tight deadline affects architecture choices)

## AI Analysis Pipeline

The AI engine must follow a strict 4-part execution flow:

1. **Data Synthesis** – Extract macro sentiment, fundamentals, price behavior, risk/liquidity signals
2. **Bull & Bear Cases** – Build independent positive and negative arguments
3. **Decision Engine** – Apply rules to map evidence → verdict + confidence
4. **Self-Validation** – Consistency check (verdict ↔ arguments), risk check, data quality, decision quality

**Key Rules:**
- No technical jargon (RSI, MACD, etc.) — use plain English
- Never hallucinate data; reduce confidence if data is weak
- Always return valid JSON only; no explanations outside JSON
- Total response under 200 words

## Output Contract (Strict JSON Format)

The backend expects this exact structure — no deviations:

```json
{
  "ticker": "string",
  "verdict": "BUY NOW | BUY SLOWLY | HOLD | STAY AWAY | SELL",
  "confidence_score": "number (0-100)",
  "risk_level": "LOW | MEDIUM | HIGH",
  "liquidity_status": "STRONG | MODERATE | WEAK",
  "summary_plain_english": "max 120 words",
  "bull_case": ["string", "string", ...],
  "bear_case": ["string", "string", ...],
  "key_drivers": ["string", "string", ...],
  "data_quality": "HIGH | MEDIUM | LOW",
  "checklist": "object (updated checklist state)"
}
```

**Validation Rules:**
- Verdict must align with bull/bear arguments
- High risk must not map to "BUY NOW"
- Confidence must reflect data strength + risk level + argument agreement
- Data quality assessment should be honest about missing/weak signals

## Checklist Execution System

The AI system manages a resumable development checklist:
- Each task has status: `DONE`, `FAILED`, or `PENDING`
- On each invocation: parse checklist, find first `FAILED` or `PENDING` task
- Execute that task and update status
- Return updated checklist in output
- **Never repeat `DONE` tasks** (prevents infinite loops)

This enables frontend to track multi-step analyses that can pause/resume.

## Critical Files & Responsibilities

### Backend
- **main.py** — FastAPI app, lifespan (symbol cache), endpoints, error handling
- **models.py** — Pydantic types (AnalysisRequest, AnalysisResponse, OHLCVBar, SignalBadge, EntryExitLevels, SignalsResponse, etc.)
- **ai_engine.py** — Claude API calls, prompt builder, JSON extraction, validation rules
- **scraper/price.py** — PSX price data, symbol caching, trend/52-week derivation
- **scraper/news.py** — Google News RSS, sentiment classification, concurrent fetching
- **scraper/financials.py** — HTML scraping, P/E/dividend/market cap extraction
- **scraper/signals.py** — Moving averages (SMA20/60/120), support/resistance clustering, volatility/volume analysis
- **.env** — API keys and configuration (ANTHROPIC_API_KEY, CLAUDE_MODEL, CORS_ORIGINS)

### Frontend
- **App.jsx** — Main component, state management, checklist persistence, concurrent API calls
- **components/SearchBar.jsx** — Ticker input with auto-uppercase
- **components/AnalysisCard.jsx** — Verdict badge, confidence gauge, bull/bear cases, key drivers
- **components/CandlestickChart.jsx** — Interactive OHLC visualization with timeframe tabs (lightweight-charts v4.2)
- **components/TechnicalSignals.jsx** — Signal badges with color-coded sentiment (bullish/bearish/neutral)
- **components/EntryExitLevels.jsx** — 6-tile grid (current price, entry zone, stop loss, targets, risk/reward)
- **components/Tooltip.jsx** — Smart tooltip positioning (above/below, prevents overflow)
- **components/ChecklistPanel.jsx** — Task status display (DONE/FAILED/PENDING)
- **components/LoadingState.jsx** — Animated progress with cycling messages
- **components/ErrorBanner.jsx** — Error display with dismissible banner

### Configuration
- **backend/.env** — ANTHROPIC_API_KEY, CLAUDE_MODEL, CORS_ORIGINS
- **frontend/.env** — VITE_API_BASE (backend URL)
- **vite.config.js** — Vite build config
- **tailwind.config.js** — Tailwind styling
- **package.json** — npm dependencies

## Development Constraints

**Hard Constraints:**
- JSON output only (no text wrapper, no markdown)
- Plain English only (no financial acronyms)
- No hallucination (missing data → lower confidence, not made-up signals)
- Response time: target 15–20 seconds (currently 12-18s achieved)

**Input Data Available:**
- Ticker symbol
- Market data (price, volume, trend)
- News & macro signals (economic, oil, USD/PKR, political)
- Financial data (fundamentals: growth, debt, dividends)
- Checklist state (to resume from checkpoint)

## Implementation Status: ✅ PHASE 2 COMPLETE

### Phase 1 (MVP) – COMPLETED ✅
- Backend FastAPI with PSX data fetching
- Frontend React with Vite + Tailwind
- AI Engine Claude integration with validation
- 30-day area chart with Recharts
- Verdict badge + Confidence gauge
- Bull/bear cases + Checklist system
- Error handling + Git repository

### Phase 2 (Signals & Charts) – COMPLETED ✅
- **Candlestick charts** – Interactive OHLC visualization with timeframe tabs (30/60/90/252 days)
- **Technical signals** – 16+ plain-English signal badges (no jargon: "buying momentum" not "RSI")
- **Entry/Exit levels** – Buy zones, stop loss, profit targets with risk/reward ratios
- **Support/Resistance** – Clustering method (3+ touches within 5%)
- **Moving averages** – SMA20, SMA60, SMA120 calculations
- **Volatility & volume signals** – Risk assessment with plain English labels
- **Current price display** – Exact PKR value in Entry & Exit Levels tiles
- **Smart tooltips** – Hover explanations on all tiles with intelligent positioning
- **Grid alignment** – Perfect 2x3 tile layout with consistent spacing

### Backend Architecture
- **Data models** – Pydantic types for requests, responses, market/news/financials data
- **Price scraper** – Fetches PSX EOD data from dps.psx.com.pk, computes trend/52-week stats
- **News scraper** – Concurrent Google News RSS fetching with keyword-based sentiment
- **Financials scraper** – BeautifulSoup HTML scraping with graceful fallback
- **Signals calculator** – Moving averages, volatility, support/resistance, momentum analysis
- **AI engine** – Claude Haiku integration with prompt builder + validation layer
- **FastAPI app** – Lifespan management for symbol cache
  - `/health` – Service health check
  - `POST /analyze` – Full AI verdict with checklist resumption
  - `GET /signals/{ticker}?timeframe={30,60,90,252}` – Technical signals with 1-hour cache

### Frontend Architecture
- **React + Vite** – Fast dev server, Tailwind CSS for styling
- **Components** – SearchBar, AnalysisCard (verdict/confidence), CandlestickChart (OHLC), TechnicalSignals (badges), EntryExitLevels (tiles), ChecklistPanel, LoadingState, ErrorBanner, Tooltip
- **State management** – Checklist persistence for analysis resumption
- **Chart rendering** – Interactive candlestick charts with SMA overlays, volume histogram, and responsive timeframe tabs

## How to Run

### 1. Backend Setup (Terminal 1)
```bash
cd D:/stock-analysis/backend
pip install -r requirements.txt
# Verify ANTHROPIC_API_KEY is set in .env
uvicorn main:app --reload --port 8000
```
- Server starts on `http://localhost:8000`
- Health check: `curl http://localhost:8000/health`
- Symbol cache loads automatically at startup (~500+ PSX symbols)

### 2. Frontend Setup (Terminal 2)
```bash
cd D:/stock-analysis/frontend
npm install
npm run dev
# Opens at http://localhost:5174 (or next available port)
```
- Hot reload enabled for development
- Connects to backend at `http://localhost:8000`

### 3. Test the App
Open `http://localhost:5174` in your browser and try analyzing PSX tickers:
- **HBL** (Habib Bank Limited)
- **ENGRO** (Engro Corporation)
- **LUCK** (Lucky Cement)
- **TRG** (Techlogix)
- **MCB** (MCB Bank)

Each analysis returns:
- Verdict badge (BUY NOW / BUY SLOWLY / HOLD / STAY AWAY / SELL)
- Confidence score (0-100%)
- Risk level & liquidity status
- Bull & bear cases
- 30-day price chart with interactive tooltip
- Analysis checklist with task status

### Direct API Testing
```bash
# Single analysis
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"ticker": "HBL", "checklist": null}'

# Resume analysis with partial checklist
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "HBL",
    "checklist": {
      "data_synthesis": "DONE",
      "bull_case_analysis": "FAILED",
      "bear_case_analysis": "PENDING",
      "decision_engine": "PENDING",
      "self_validation": "PENDING"
    }
  }'
```

## Important Implementation Details

### Import Paths (Backend)
- All backend imports use **relative imports** (not `from backend.models`) so the app works when run from the backend directory
- When running: `cd backend && python -m uvicorn main:app --reload`

### PSX Data Sources
- **Price data**: `https://dps.psx.com.pk/timeseries/eod/{TICKER}?length=252` returns JSON with unix timestamps and OHLCV
- **Symbol list**: Cached at startup from `https://dps.psx.com.pk/symbols` (~131KB, valid for session)
- **Company info**: HTML scraped from `https://dps.psx.com.pk/company/{TICKER}` (P/E, dividend, market cap)
- **News**: Google News RSS (no API key needed, public feed)

### Checklist Resume Logic
- First call: send `{"checklist": null}` → AI receives all tasks as PENDING
- Subsequent calls: send back the `checklist` object from the previous response
- AI resumes from first FAILED or PENDING task, never repeats DONE tasks
- Enables multi-step analysis with pause/resume capability

### Chart Data
- Response includes `recent_prices` array with 30 days of history
- Each entry: `{date: "YYYY-MM-DD", close: price_in_pkr, volume: shares_traded}`
- Frontend PriceChart uses Recharts AreaChart with dynamic coloring (green/red trend)

### Error Handling
- Invalid ticker: returns 404 with message
- Lowercase input: auto-converted to uppercase
- Missing news/financials: gracefully degraded (AI reduces confidence, continues)
- API timeout: returns 503 with service error message

### Performance Notes
- Data fetch (price + news + financials) runs in parallel → ~2 seconds total
- Claude Haiku API call → ~10-12 seconds
- Full pipeline SLA: 12-18 seconds (target 15-20s met)
- Symbol cache: loaded once at startup, reused for all requests

## Testing Approach

- **Health check**: `curl http://localhost:8000/health` → confirms model is ready
- **Real ticker test**: Try HBL, ENGRO, LUCK with different verdict scenarios
- **Error test**: Send invalid ticker (e.g., "XXXX") → should return 404
- **Case test**: Send "hbl" (lowercase) → should auto-uppercase to HBL
- **Checklist test**: Send back checklist with FAILED/PENDING tasks → should resume
- **Frontend test**: Search for tickers in browser → verify chart displays 30 points

## Phase 3 Roadmap (Upcoming)

### Planned Features
- **Advanced chart indicators** – Keep plain-English descriptions (moving average crossovers as "momentum points")
- **Historical analysis tracking** – Store past verdicts and compare accuracy over time
- **Comparative analysis** – Side-by-side comparison of multiple tickers
- **Backtesting engine** – Test verdict accuracy against historical price movements
- **Watchlist management** – Save favorite tickers and track changes
- **Alert system** – Notify when stock hits target price or crosses key levels
- **Real-time data** – Replace EOD with intraday updates from PSX DPS API
- **Database persistence** – Store analysis history and user preferences
- **Mobile app** – React Native version for iOS/Android
- **PDF export** – Generate analysis reports

### Architecture Improvements
- Implement Redis caching for signals (beyond 1-hour TTL)
- Add WebSocket support for real-time price updates
- Refactor AI engine for streaming responses (faster UX feedback)
- Add authentication layer for user-specific data
- Implement rate limiting and abuse prevention

## Known Limitations & Future Improvements

### Current Limitations
1. **Financials scraping** — PSX company page layout may change, breaking scraper. Fallback to `data_available=False` works but AI reduces confidence.
2. **News availability** — Google News RSS sometimes returns fewer articles depending on region/freshness. Gracefully degrades.
3. **Market hours** — EOD data doesn't update until PSX closes (3:30 PM PKT). Pre-market requests show previous day's data.
4. **Browser storage** — Checklist state lives only in frontend memory. Refresh loses progress (user must restart).
5. **No user persistence** — Each session is independent. No historical analysis storage.

### Potential Improvements
- **Real-time data** — Replace EOD with intraday data from PSX DPS API for live updates
- **Database** — Store analysis history, user watchlists, saved verdicts
- **Alerts** — Notify users when stock hits target price or crosses key levels
- **Comparative analysis** — Compare multiple tickers side-by-side
- **Backtesting** — Test verdict accuracy against historical price movements
- **Advanced charts** — Candlestick, moving averages, technical indicators (while keeping plain English descriptions)
- **Mobile app** — React Native version for iOS/Android
- **Export** — PDF reports of analysis

## Troubleshooting

**"ModuleNotFoundError: No module named 'backend'"**
- Ensure you're running from the backend directory: `cd D:/stock-analysis/backend`
- Use relative imports (fixed in current codebase)

**"Ticker not found on PSX"**
- Ticker must be valid PSX symbol (check against cached symbols)
- Case-insensitive, but must be 2-10 characters alphabetic
- Examples: HBL, ENGRO, LUCK, TRG, MCB

**"AI parsing error"**
- Claude returned invalid JSON or malformed response
- Rare, but can happen if prompt is changed significantly
- Check SYSTEM_PROMPT in ai_engine.py hasn't deviated from requirements.md

**"No chart data showing"**
- Verify `recent_prices` is in API response: `curl http://localhost:8000/analyze | grep recent_prices`
- Should see 30 entries with date, close, volume
- Frontend PriceChart component requires this field

**Port 5173/8000 already in use**
- Kill the process: `lsof -i :8000` then `kill -9 <PID>`
- Or just start on different port: `uvicorn main:app --port 8001`
