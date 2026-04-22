# Intelli-Trade: AI-Powered Stock Analysis for PSX

An intelligent financial decision engine for the Pakistan Stock Exchange (PSX) that combines AI-driven sentiment analysis, technical signals, and fundamental analysis to provide actionable investment verdicts in **15–20 seconds**.

![Status](https://img.shields.io/badge/Status-Phase%202%20Complete-brightgreen) ![Model](https://img.shields.io/badge/AI-Claude%20Haiku-blue) ![License](https://img.shields.io/badge/License-MIT-green)

---

## 🚀 Features

### Stock Analysis (PSX Tickers) – Phase 1 & 2 ✅ COMPLETE

#### Phase 1: Core MVP ✅
- **AI Verdict Engine** – Synthesizes market data, news sentiment, and fundamentals into actionable verdicts
- **Confidence & Risk Assessment** – Data-driven confidence scores (0–100%) with risk levels (LOW/MEDIUM/HIGH)
- **Bull & Bear Cases** – Dual-perspective analysis showing positive and negative factors
- **Price Charts** – 30-day interactive area chart with trend visualization
- **Analysis Checklist** – Resumable multi-step analysis with task tracking

#### Phase 2: Signals & Charts ✅
- **Candlestick Charts** – Interactive OHLC visualization with:
  - Color-coded candles (green=up, red=down)
  - Volume histogram overlay
  - SMA20 & SMA60 moving average lines
  - Timeframe tabs (30/60/90/252 days)
  
- **Technical Signals** – 16+ plain-English signal badges (no jargon):
  - Momentum indicators ("strong buying momentum" not "RSI")
  - Volatility assessment ("wide price swings" not "Bollinger Bands")
  - Volume signals ("heavy trading interest" not "OBV")
  - Trend detection (uptrend/downtrend/sideways)
  - Support/Resistance zones

- **Entry/Exit Levels** – Trading guidance with:
  - Buy entry zones
  - Stop-loss levels for risk management
  - Profit targets (T1 & T2)
  - Risk/Reward ratio visualization
  - Current price display

- **Smart Tooltips** – Context-sensitive explanations on hover with intelligent positioning

---

## 📊 Architecture

### Backend (FastAPI)
```
backend/
├── main.py                 # FastAPI app, endpoints, error handling
├── models.py              # Pydantic data models
├── ai_engine.py           # Claude integration with validation
└── scraper/
    ├── price.py           # PSX EOD data fetching
    ├── news.py            # Google News sentiment analysis
    ├── financials.py      # Company fundamentals scraping
    └── signals.py         # Technical indicator calculations
```

### Frontend (React + Vite)
```
frontend/
├── src/
│   ├── App.jsx            # Main component, state management
│   ├── components/
│   │   ├── SearchBar.jsx
│   │   ├── AnalysisCard.jsx
│   │   ├── CandlestickChart.jsx    # Phase 2: Interactive charts
│   │   ├── TechnicalSignals.jsx    # Phase 2: Signal badges
│   │   ├── EntryExitLevels.jsx     # Phase 2: Trading levels
│   │   ├── Tooltip.jsx
│   │   ├── ChecklistPanel.jsx
│   │   ├── LoadingState.jsx
│   │   └── ErrorBanner.jsx
│   └── index.css
├── tailwind.config.js
└── vite.config.js
```

---

## 🔌 API Endpoints

### `/POST /analyze`
Full AI analysis with checklist support.

**Request:**
```json
{
  "ticker": "HBL",
  "checklist": null
}
```

**Response:**
```json
{
  "ticker": "HBL",
  "verdict": "BUY NOW",
  "confidence_score": 78,
  "risk_level": "MEDIUM",
  "liquidity_status": "STRONG",
  "summary_plain_english": "Strong upward momentum with solid fundamentals...",
  "bull_case": ["Growing profitability", "Strong dividend yield"],
  "bear_case": ["Economic slowdown risk", "Rising interest rates"],
  "key_drivers": ["Dividend income", "Market recovery"],
  "data_quality": "HIGH",
  "recent_prices": [...],
  "checklist": {
    "data_synthesis": "DONE",
    "bull_case_analysis": "DONE",
    "bear_case_analysis": "DONE",
    "decision_engine": "DONE",
    "self_validation": "DONE"
  }
}
```

### `GET /signals/{ticker}?timeframe={30|60|90|252}`
Technical signals, moving averages, support/resistance, entry/exit levels (1-hour cache).

**Response:**
```json
{
  "ticker": "HBL",
  "timeframe": 30,
  "ohlcv_data": [
    {"date": "2024-03-15", "open": 1234.5, "high": 1245.3, "low": 1230.2, "close": 1242.1, "volume": 1500000}
  ],
  "moving_averages": {
    "sma20": 1238.4,
    "sma60": 1235.2,
    "sma120": 1232.1
  },
  "support_resistance": {
    "support": 1220.5,
    "resistance": 1250.0
  },
  "signal_badges": [
    {"text": "Strong buying momentum", "sentiment": "BULLISH", "category": "momentum"},
    {"text": "Heavy trading interest today", "sentiment": "BULLISH", "category": "volume"}
  ],
  "entry_exit_levels": {
    "current_price": 1242.1,
    "entry_zone_low": 1235.0,
    "entry_zone_high": 1240.0,
    "stop_loss": 1210.0,
    "target1": 1265.0,
    "target2": 1285.0,
    "risk_reward_ratio": 2.5
  }
}
```

### `GET /health`
Service health check.

---

## 🚀 Getting Started

### Prerequisites
- Python 3.9+ with `pip`
- Node.js 16+ with `npm`
- Anthropic API key ([get one here](https://console.anthropic.com))

### 1. Backend Setup

```bash
cd backend
pip install -r requirements.txt
```

Create `.env`:
```env
ANTHROPIC_API_KEY=sk-ant-...
CLAUDE_MODEL=claude-3-5-haiku-20241022
CORS_ORIGINS=http://localhost:5174
```

Start the server:
```bash
uvicorn main:app --reload --port 8000
```

Health check:
```bash
curl http://localhost:8000/health
```

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Opens at `http://localhost:5174`

### 3. Test the App

Open `http://localhost:5174` and analyze PSX tickers:
- **HBL** (Habib Bank Limited)
- **ENGRO** (Engro Corporation)
- **LUCK** (Lucky Cement)
- **TRG** (Techlogix)
- **MCB** (MCB Bank)

---

## 🧪 Testing

### Direct API Testing
```bash
# Full analysis
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"ticker": "HBL", "checklist": null}'

# Technical signals
curl http://localhost:8000/signals/HBL?timeframe=30
```

### Test Scenarios
- ✅ Valid ticker analysis
- ✅ Lowercase input (auto-converted to uppercase)
- ✅ Invalid ticker (returns 404)
- ✅ Checklist resumption (FAILED/PENDING tasks)
- ✅ Chart data validation (30 price points)
- ✅ Signal badge rendering

---

## 📈 Data Sources

| Component | Source | Refresh |
|-----------|--------|---------|
| **Price Data** | PSX DPS API (`dps.psx.com.pk`) | EOD (3:30 PM PKT) |
| **News Sentiment** | Google News RSS | Real-time |
| **Fundamentals** | PSX Company Pages | Daily |
| **Symbols Cache** | PSX Symbol List | Session startup |

---

## ⚙️ Configuration

### Backend (.env)
```env
ANTHROPIC_API_KEY=sk-ant-...           # Required: Your API key
CLAUDE_MODEL=claude-3-5-haiku-20241022 # AI model
CORS_ORIGINS=http://localhost:5174     # Frontend URL
```

### Frontend (.env)
```env
VITE_API_BASE=http://localhost:8000    # Backend URL
```

---

## 🔒 Constraints & Validation

### AI Output Rules
- ✅ **No hallucination** – Missing data reduces confidence, not invented
- ✅ **Plain English only** – No acronyms (RSI, MACD, EMA)
- ✅ **Valid JSON** – Always valid, never markdown wrapper
- ✅ **Verdict alignment** – Confidence matches bull/bear/risk assessment
- ✅ **Response time** – Target 15–20 seconds (current: 12–18s)

### UI/UX Rules
- ✅ **2×3 grid layout** – Perfect tile alignment with consistent spacing
- ✅ **Smart tooltips** – Context on hover, prevents viewport overflow
- ✅ **Color coding** – Sentiment-based (green=bullish, red=bearish, yellow=neutral)
- ✅ **Responsive design** – Desktop (2-col), mobile (1-col)
- ✅ **Accessibility** – Clear labels, keyboard navigation, high contrast

---

## 📊 Performance

| Component | Target | Actual |
|-----------|--------|--------|
| Data fetching | ~2s | ✅ 2–3s |
| AI analysis | ~10–12s | ✅ 10–12s |
| Signals endpoint | ~3–5s | ✅ 3–5s |
| Full pipeline | 15–20s | ✅ 12–18s |

**Architecture:** Concurrent data fetching + non-blocking API calls for fast UX.

---

## 🛠️ Development

### Adding a New Signal
1. Calculate metric in `scraper/signals.py`
2. Add to `SignalBadge` list in response
3. Create Tooltip.jsx entry with plain English
4. Test with real ticker

### Updating AI Prompt
- Edit `SYSTEM_PROMPT` in `ai_engine.py`
- Keep constraints from `requirements.md`
- Test with multiple tickers
- Verify JSON structure doesn't change

### Frontend Component Updates
- Use Tailwind for styling (no custom CSS)
- Add Tooltip wrapper for hover text
- Test responsive layout (desktop + mobile)
- Verify accessibility (keyboard, screen reader)

---

## ⚠️ Known Limitations

1. **Financials scraping** – PSX page layout changes may break scraper
2. **News availability** – Google RSS varies by region/freshness
3. **Market hours** – EOD data updates only after PSX close (3:30 PM PKT)
4. **Browser storage** – Checklist lost on refresh (requires restart)
5. **No user persistence** – Each session is independent

---

## 🚀 Phase 3: Mutual Fund Analysis (In Development)

Extends Intelli-Trade to analyze Pakistan mutual funds listed on MUFAP alongside PSX stocks.

### Phase 3 Features ⏳
- **Separate Mutual Fund Tab** – Independent UI section for fund analysis
- **Fund Search & Filtering** – Search by name/code, filter by type (equity/fixed income/balanced/index/VPS)
- **AI-Powered Fund Verdict** – Same verdict system (BUY NOW/SLOWLY/HOLD/STAY AWAY/SELL) adapted for funds
- **Fund Performance Analysis** – Historical returns (1Y/3Y/5Y), NAV trends, benchmark comparison
- **Risk Assessment** – Sharpe ratio, volatility, beta (plain English labels)
- **Cost-Benefit Analysis** – Expense ratio, front-end load, fee vs return comparison
- **Fund Composition Display** – Top holdings, sector allocation, asset mix breakdown
- **Fund Manager Assessment** – Track record, tenure, AUM management, performance consistency
- **Candlestick Charts** – Interactive NAV trends with timeframe tabs (reusing Phase 2 components)
- **Technical Signals** – Performance signals adapted for mutual funds
- **Side-by-Side Comparison** – Compare 2-3 mutual funds with verdict comparison

### Data Sources
- **MUFAP** – Pakistan Mutual Funds Association data (fund list, NAV, performance)
- **Fund Details** – Scrape from mufap.com.pk (composition, manager info, fees)
- **Caching Strategy** – 1-day TTL for NAV/performance, 1-week for holdings/list

### Backend Enhancements
- `GET /funds` – List all available MUFAP funds with filtering
- `POST /analyze/fund` – Full AI verdict for a single fund (~12-18s)
- `GET /signals/fund/{code}?timeframe=...` – Fund performance signals (~3-5s)
- `GET /compare/funds?codes=...` – Side-by-side comparison of 2-3 funds
- `scraper/mutual_funds.py` – MUFAP data extraction and caching

### Frontend Components
- **MutualFundSearchBar** – Fund search with type filtering
- **FundAnalysisCard** – Verdict badge, confidence, risk, investment horizon
- **FundPerformanceChart** – Interactive NAV chart with timeframe tabs
- **FundCompositionDisplay** – Holdings grid, sector pie chart, asset allocation
- **FundMetricsPanel** – 6-tile grid (expense ratio, Sharpe, volatility, beta, etc.)
- **FundComparisonView** – Side-by-side analysis for 2-3 funds
- **ManagerAssessment** – Fund manager profile and track record

### Implementation Timeline
**6-7 weeks, high priority** (Start immediately after Phase 2 merge)
1. Data layer & MUFAP scraping (Week 1-2)
2. AI engine with fund-specific logic (Week 2-3)
3. Backend endpoints & caching (Week 3-4)
4. Frontend components & search (Week 4-5)
5. Comparison view & integration (Week 5-6)
6. Testing & optimization (Week 6-7)

---

## 🎯 Future Roadmap (Phase 4+)

- 📊 Historical verdict tracking & accuracy backtesting
- 📈 Portfolio construction recommendations (stocks + funds)
- 🔔 Real-time alerts (price targets, key levels, fund rebalancing)
- 💾 Database persistence (watchlists, analysis history, user preferences)
- 📱 Mobile app (React Native)
- ⚡ Real-time intraday data (replace EOD)
- 🔐 User authentication & multi-device sync

---

## 🤝 Contributing

This project is under active development. For bug reports or feature requests, please check the requirements document in `requirements.md`.

---

## 📚 Documentation

- **Architecture Guide** – See `CLAUDE.md`
- **Technical Requirements** – See `requirements.md`
- **API Reference** – See `CLAUDE.md` section "Output Contract"

---

## 🙋 Support

**Getting Started?** Follow the "Getting Started" section above.

**API Not responding?** Check backend is running on `http://localhost:8000/health`

**Chart not showing?** Ensure `recent_prices` is in API response and `recent_prices` array has 30 entries.

**AI returning invalid JSON?** Check `SYSTEM_PROMPT` in `ai_engine.py` matches `requirements.md`.

---

**Built with ❤️ for the Pakistan Stock Exchange**
