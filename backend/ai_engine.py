import json
import re
import anthropic
from models import MarketData, NewsData, FinancialsData, AnalysisResponse

SYSTEM_PROMPT = """You are the core intelligence and execution agent for a production-grade AI-powered web application called "Intelli-Trade" for Pakistan Stock Exchange (PSX).

Your responsibility includes:
1. Acting as an AI financial decision engine
2. Supporting backend API requirements
3. Ensuring output correctness and consistency
4. Managing development checklist execution with resume capability

APPLICATION CONTEXT:

- Frontend: React.js (displays verdict badge, summary, risk, confidence, chart)
- Backend: FastAPI (expects strict JSON responses)
- Response time target: 15–20 seconds
- Output is directly consumed by UI (no formatting errors allowed)

--------------------------------------------------
STRICT RULES:

- Do NOT use technical jargon (RSI, MACD, etc.)
- Always use plain English
- Do NOT hallucinate missing data
- If data is weak → reduce confidence score
- Always return valid JSON only
- Do NOT include explanations outside JSON
- Keep total response under 200 words

--------------------------------------------------
TASK EXECUTION FLOW:

========================
PART A: AI ANALYSIS
========================

STEP 1: DATA SYNTHESIS
- Extract key signals:
  - Macro sentiment (economy, oil, USD/PKR, political factors)
  - Fundamentals (growth, debt, dividends)
  - Price behavior (trend, buying/selling pressure)
  - Risk & liquidity (volume, sector risks)

STEP 2: BULLISH CASE
- Identify strongest positive signals
- Define growth drivers
- Best-case scenario

STEP 3: BEARISH CASE
- Identify risks and red flags
- Define downside risks
- Worst-case scenario

STEP 4: DECISION ENGINE
Apply rules:
- Strong upside + low risk → BUY NOW
- Moderate upside → BUY SLOWLY
- Balanced → HOLD
- High uncertainty → STAY AWAY
- Strong downside → SELL

Assign:
- Confidence score (0–100)
- Risk level (LOW/MEDIUM/HIGH)
- Liquidity status (STRONG/MODERATE/WEAK)

========================
PART B: SELF-VALIDATION (AI TESTING LAYER)
========================

Before finalizing verdict, validate:

1. CONSISTENCY CHECK
- Does verdict align with bull & bear arguments?
- If conflict → reduce confidence

2. RISK CHECK
- If high risk exists → avoid BUY NOW

3. DATA QUALITY CHECK
- Missing/weak data → lower confidence

4. DECISION QUALITY CHECK
- Avoid overly aggressive decisions without strong support

If any check fails:
- Adjust verdict or confidence accordingly

========================
PART C: CHECKLIST EXECUTION SYSTEM
========================

You must manage and update the development checklist.

RULES:
- Each task has: DONE, FAILED, or PENDING
- After completing a task → mark DONE
- If task fails → mark FAILED and STOP execution
- On restart → resume from first FAILED or PENDING task
- NEVER repeat DONE tasks

PROCESS:

1. Parse checklist_json
2. Identify first FAILED or PENDING task
3. Simulate execution of that task
4. Update its status:
   - Success → DONE
   - Failure → FAILED
5. Return updated checklist

========================
PART D: OUTPUT FORMAT
========================

Return STRICT JSON ONLY:

{
  "ticker": "{ticker}",
  "verdict": "BUY NOW | BUY SLOWLY | HOLD | STAY AWAY | SELL",
  "confidence_score": 0-100,
  "risk_level": "LOW | MEDIUM | HIGH",
  "liquidity_status": "STRONG | MODERATE | WEAK",
  "summary_plain_english": "Max 120 words explanation",
  "bull_case": [
    "Key positive factor",
    "Another positive factor"
  ],
  "bear_case": [
    "Key risk factor",
    "Another risk factor"
  ],
  "key_drivers": [
    "Primary driver",
    "Secondary driver"
  ],
  "data_quality": "HIGH | MEDIUM | LOW",
  "checklist": {updated_checklist_json}
}

--------------------------------------------------
FINAL CONSTRAINTS:

- Total response under 200 words
- No repetition
- JSON must be valid
- Verdict must align with reasoning
- Confidence must reflect:
  - Data strength
  - Risk level
  - Bull vs Bear agreement"""


def _build_user_prompt(
    market: MarketData,
    news: NewsData,
    financials: FinancialsData,
    checklist: dict,
) -> str:
    """Fill requirements.md template with real data."""
    market_section = f"""Ticker: {market.ticker} ({market.company_name})
Sector: {market.sector}
Current Price: PKR {market.current_price}
Open Price: PKR {market.open_price}
Price Change Today: {market.price_change_pct:+.2f}%
Today's Volume: {market.current_volume:,.0f} shares
30-Day Average Volume: {market.avg_volume_30d:,.0f} shares
Volume vs Average: {((market.current_volume / market.avg_volume_30d) - 1) * 100:+.1f}%
52-Week High: PKR {market.week_52_high}
52-Week Low: PKR {market.week_52_low}
Current vs 52W High: {market.price_vs_52w_high_pct:.1f}%
Trend Direction: {market.trend_direction}"""

    news_section = f"""Company News Headlines (last 7 days):
{chr(10).join(f"- {h}" for h in news.company_headlines[:7]) if news.company_headlines else "- No recent company-specific news found"}

Pakistan Macro Headlines:
{chr(10).join(f"- {h}" for h in news.macro_headlines[:5]) if news.macro_headlines else "- No macro news found"}

Overall Sentiment Signal: {news.sentiment_hint}"""

    if financials.data_available:
        fin_section = f"""P/E Ratio: {financials.pe_ratio or "Not available"}
Dividend Yield: {financials.dividend_yield or "Not available"}%
Market Cap: PKR {financials.market_cap_bn_pkr or "Not available"} Billion"""
    else:
        fin_section = "Financial fundamentals not available for this ticker — reduce confidence accordingly."

    checklist_section = json.dumps(
        checklist
        or {
            "data_synthesis": "PENDING",
            "bull_case_analysis": "PENDING",
            "bear_case_analysis": "PENDING",
            "decision_engine": "PENDING",
            "self_validation": "PENDING",
        },
        indent=2,
    )

    return f"""Ticker: {market.ticker}

Market Data:
{market_section}

News & Macro Signals:
{news_section}

Financial Data:
{fin_section}

Checklist State:
{checklist_section}

--------------------------------------------------
TASK EXECUTION FLOW:
[Follow PART A: AI ANALYSIS → PART B: SELF-VALIDATION → PART C: CHECKLIST → PART D: OUTPUT FORMAT as defined in your system instructions]
Return STRICT JSON ONLY. No text outside JSON."""


def _validate_response(data: dict) -> dict:
    """Python-side validation layer — enforce rules before returning."""
    verdict = data.get("verdict", "HOLD")
    risk = data.get("risk_level", "HIGH")
    confidence = data.get("confidence_score", 50)
    bull = data.get("bull_case", [])
    bear = data.get("bear_case", [])

    # Rule 1: HIGH risk → no BUY NOW
    if risk == "HIGH" and verdict == "BUY NOW":
        data["verdict"] = "BUY SLOWLY"
        data["confidence_score"] = min(confidence, 55)

    # Rule 2: More bear than bull signals → cap confidence
    if len(bear) > len(bull) and verdict in ["BUY NOW", "BUY SLOWLY"]:
        data["confidence_score"] = min(confidence, 60)

    # Rule 3: LOW data quality → cap confidence
    if data.get("data_quality") == "LOW":
        data["confidence_score"] = min(confidence, 50)

    # Rule 4: Clamp confidence
    data["confidence_score"] = max(0, min(100, data["confidence_score"]))

    # Rule 5: Validate verdict enum
    valid_verdicts = {"BUY NOW", "BUY SLOWLY", "HOLD", "STAY AWAY", "SELL"}
    if data["verdict"] not in valid_verdicts:
        data["verdict"] = "HOLD"

    return data


async def run_analysis(
    market: MarketData,
    news: NewsData,
    financials: FinancialsData,
    checklist: dict | None,
    api_key: str,
    model: str,
) -> AnalysisResponse:
    """Call Claude API and return validated response."""
    client_ai = anthropic.AsyncAnthropic(api_key=api_key)
    user_prompt = _build_user_prompt(market, news, financials, checklist)

    message = await client_ai.messages.create(
        model=model,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw_text = message.content[0].text.strip()

    # Extract JSON (handles markdown wrappers)
    json_match = re.search(r"\{[\s\S]*\}", raw_text)
    if not json_match:
        raise ValueError("Claude did not return valid JSON")

    data = json.loads(json_match.group())
    data = _validate_response(data)
    data["recent_prices"] = market.recent_prices
    data["current_price"] = market.current_price

    return AnalysisResponse(**data)
