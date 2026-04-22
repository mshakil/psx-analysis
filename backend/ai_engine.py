import json
import re
import anthropic
from models import (
    MarketData, NewsData, FinancialsData, AnalysisResponse,
    FundInfoData, FundNavHistory, FundPerformanceData, FundCompositionData,
    FundAnalysisResponse,
)

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


# ============================================
# PHASE 3: MUTUAL FUND ANALYSIS ENGINE
# ============================================

FUND_SYSTEM_PROMPT = """You are the mutual fund analysis engine for Intelli-Trade, Pakistan's AI-powered investment platform.

Your responsibility is to analyze Pakistan mutual funds listed on MUFAP and provide clear, actionable verdicts.

APPLICATION CONTEXT:
- Frontend: React.js consumes your JSON directly
- Backend: FastAPI with strict Pydantic validation
- Response time target: 12–18 seconds
- All output is consumed by UI — zero formatting errors allowed

--------------------------------------------------
STRICT RULES:
- Do NOT use technical finance jargon (Sharpe, Beta, NAV, Standard Deviation as terms)
- Instead use plain English: "risk-adjusted return", "price stability", "market sensitivity"
- Do NOT hallucinate performance data — if data missing, say so and reduce confidence
- Always return valid JSON only — no text outside JSON
- Keep summary_plain_english under 120 words

--------------------------------------------------
TASK EXECUTION FLOW:

========================
PART A: FUND ANALYSIS
========================

STEP 1: FUND CHARACTERIZATION
- Identify the fund type (stocks/bonds/mixed/index/pension)
- Classify the risk profile based on portfolio composition
- Assess manager experience (years of tenure, consistency)
- Evaluate cost structure: total fees vs delivered returns

STEP 2: PERFORMANCE ANALYSIS
- Compare 1-year, 3-year, 5-year returns
- Assess performance vs benchmark (outperforming/in-line/underperforming)
- Evaluate risk-adjusted return quality
- Assess price stability and downside risk

STEP 3: COST-BENEFIT EVALUATION
- Total annual cost = expense ratio + amortized front-end load
- Is the fund earning more than it costs in fees?
- Compare cost vs peer funds of same type
- Verdict on whether fees are justified

STEP 4: SUITABILITY & VERDICT
Fund-specific verdict rules:
- BUY NOW: Outperforming benchmark + fees below 2% + strong manager (5+ years) + low cost
- BUY SLOWLY: Solid performance (within 2% of benchmark) + moderate fees + acceptable risk
- HOLD: Adequate performance, no compelling reason to switch, moderate fees
- STAY AWAY: Consistently underperforming benchmark + high fees + weak/new manager
- SELL: Strong underperformance (5%+ below benchmark), fund size declining, better alternatives available

Risk rules:
- Equity funds: generally HIGH risk
- Balanced funds: generally MEDIUM risk
- Fixed income/Income funds: generally LOW-MEDIUM risk
- Index funds: risk matches underlying market
- VPS funds: MEDIUM risk (long-term pension focus)

Investment horizon rules:
- Equity funds → LONG_TERM
- Fixed income funds → SHORT_TERM or MEDIUM_TERM
- Balanced funds → MEDIUM_TERM
- Index funds → LONG_TERM
- VPS funds → LONG_TERM

========================
PART B: SELF-VALIDATION
========================

Before finalizing verdict:
1. CONSISTENCY CHECK: Does verdict align with performance + cost data?
2. RISK CHECK: Is risk_level consistent with fund_type?
3. DATA QUALITY CHECK: If performance data missing → cap confidence at 50
4. VERDICT CALIBRATION: HIGH risk + HIGH fees → avoid BUY NOW

If any check fails → adjust verdict or reduce confidence.

========================
PART C: CHECKLIST EXECUTION
========================
Same rules as stock checklist:
- DONE/FAILED/PENDING
- Resume from first FAILED or PENDING
- Never repeat DONE tasks

========================
PART D: OUTPUT FORMAT
========================

Return STRICT JSON ONLY — no text outside JSON:

{
  "fund_code": "{fund_code}",
  "fund_name": "{fund_name}",
  "fund_type": "EQUITY|FIXED_INCOME|BALANCED|INDEX|VPS|OTHER",
  "verdict": "BUY NOW | BUY SLOWLY | HOLD | STAY AWAY | SELL",
  "confidence_score": 0-100,
  "risk_level": "LOW | MEDIUM | HIGH",
  "investment_horizon": "SHORT_TERM | MEDIUM_TERM | LONG_TERM",
  "summary_plain_english": "Max 120 words explanation in plain English",
  "manager_assessment": "One sentence on manager track record and tenure",
  "cost_benefit_analysis": "One sentence on whether fees are worth it",
  "composition_breakdown": {
    "top_holdings": ["holding1", "holding2"],
    "sector_allocation": {"sector_name": percentage_float},
    "asset_mix": {"asset_type": percentage_float}
  },
  "performance_metrics": {
    "returns_1y": null_or_float,
    "returns_3y": null_or_float,
    "returns_5y": null_or_float,
    "benchmark_comparison": "outperforming|in_line|underperforming",
    "sharpe_ratio": null_or_float,
    "volatility": "LOW | MEDIUM | HIGH",
    "beta": null_or_float
  },
  "fee_structure": {
    "expense_ratio": null_or_float,
    "front_end_load": null_or_float,
    "total_cost": null_or_float,
    "fee_assessment": "expensive|fair|cheap"
  },
  "bull_case": ["key positive 1", "key positive 2"],
  "bear_case": ["key risk 1", "key risk 2"],
  "key_drivers": ["primary driver", "secondary driver"],
  "data_quality": "HIGH | MEDIUM | LOW",
  "checklist": {updated_checklist_json}
}

--------------------------------------------------
FINAL CONSTRAINTS:
- Total JSON response under 300 words
- No repetition between bull_case, bear_case, key_drivers
- JSON must be valid (Pydantic validates immediately)
- Verdict must reflect both performance AND cost
- Confidence must be honest: missing data = lower confidence
"""


def _build_fund_user_prompt(
    fund_info: FundInfoData,
    nav_history: FundNavHistory,
    performance: FundPerformanceData,
    composition: FundCompositionData,
    checklist: dict,
) -> str:
    """Build fund analysis user prompt with labeled sections."""
    fund_section = f"""Fund Code: {fund_info.fund_code}
Fund Name: {fund_info.fund_name}
Fund Type: {fund_info.fund_type}
AMC (Asset Management Company): {fund_info.amc_name}
Fund Size: PKR {fund_info.aum_bn_pkr or "Not available"} Billion
Inception Date: {fund_info.inception_date or "Not available"}"""

    nav_1w = f"{nav_history.nav_1w_change_pct:+.2f}%" if nav_history.nav_1w_change_pct is not None else "Not available"
    nav_1m = f"{nav_history.nav_1m_change_pct:+.2f}%" if nav_history.nav_1m_change_pct is not None else "Not available"
    trend = "Rising" if nav_history.nav_1m_change_pct and nav_history.nav_1m_change_pct > 0 else "Declining" if nav_history.nav_1m_change_pct else "Unknown"

    nav_section = f"""Current NAV: PKR {nav_history.current_nav or "Not available"}
NAV Change (1 week): {nav_1w}
NAV Change (1 month): {nav_1m}
Price Trend: {trend}"""

    perf_section = f"""1-Year Return: {performance.returns_1y or "Not available"}%
3-Year Return (annualized): {performance.returns_3y or "Not available"}%
5-Year Return (annualized): {performance.returns_5y or "Not available"}%
Benchmark 1-Year Return: {performance.benchmark_returns_1y or "Not available"}%
Risk-Adjusted Score (Sharpe Ratio): {performance.sharpe_ratio or "Not available"}
Volatility (Price movement stability): {performance.std_deviation or "Not available"}%
Market Sensitivity (Beta): {performance.beta or "Not available"}"""

    fee_section = f"""Annual Management Fee (Expense Ratio): {fund_info.expense_ratio or "Not available"}%
One-Time Entry Fee (Front-End Load): {fund_info.front_end_load or "Not available"}%"""

    manager_section = f"""Fund Manager Name: {fund_info.manager_name or "Not available"}
Manager Tenure: {fund_info.manager_tenure_years or "Not available"} years"""

    composition_section = f"""Top 10 Holdings:
{chr(10).join(f"- {h}" for h in composition.top_holdings) if composition.top_holdings else "- Not available"}

Sector Allocation:
{chr(10).join(f"- {sector}: {pct}%" for sector, pct in composition.sector_allocation.items()) if composition.sector_allocation else "- Not available"}

Asset Mix:
{chr(10).join(f"- {asset}: {pct}%" for asset, pct in composition.asset_mix.items()) if composition.asset_mix else "- Not available"}"""

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

    return f"""Fund: {fund_info.fund_code} ({fund_info.fund_name})

Fund Identity:
{fund_section}

Current NAV:
{nav_section}

Performance History:
{perf_section}

Fee Structure:
{fee_section}

Fund Manager:
{manager_section}

Portfolio Composition:
{composition_section}

Checklist State:
{checklist_section}

--------------------------------------------------
TASK EXECUTION FLOW:
[Follow PART A: FUND ANALYSIS → PART B: SELF-VALIDATION → PART C: CHECKLIST → PART D: OUTPUT FORMAT as defined in your system instructions]
Return STRICT JSON ONLY. No text outside JSON."""


def _validate_fund_response(data: dict) -> dict:
    """Python-side validation for fund analysis — enforce rules before returning."""
    verdict = data.get("verdict", "HOLD")
    risk = data.get("risk_level", "HIGH")
    confidence = data.get("confidence_score", 50)
    bull = data.get("bull_case", [])
    bear = data.get("bear_case", [])
    fund_type = data.get("fund_type", "OTHER")

    # Rule 1: HIGH risk + BUY NOW → BUY SLOWLY, cap confidence at 55
    if risk == "HIGH" and verdict == "BUY NOW":
        data["verdict"] = "BUY SLOWLY"
        data["confidence_score"] = min(confidence, 55)

    # Rule 2: bear > bull on buy verdict → cap confidence at 60
    if len(bear) > len(bull) and verdict in ["BUY NOW", "BUY SLOWLY"]:
        data["confidence_score"] = min(confidence, 60)

    # Rule 3: data_quality=LOW → cap confidence at 45 (stricter than stock's 50)
    if data.get("data_quality") == "LOW":
        data["confidence_score"] = min(confidence, 45)

    # Rule 4: Clamp confidence 0-100
    data["confidence_score"] = max(0, min(100, data["confidence_score"]))

    # Rule 5: Validate verdict enum
    valid_verdicts = {"BUY NOW", "BUY SLOWLY", "HOLD", "STAY AWAY", "SELL"}
    if data.get("verdict") not in valid_verdicts:
        data["verdict"] = "HOLD"

    # Rule 6: Validate fund_type enum
    valid_fund_types = {"EQUITY", "FIXED_INCOME", "BALANCED", "INDEX", "VPS", "OTHER"}
    if data.get("fund_type") not in valid_fund_types:
        data["fund_type"] = "OTHER"

    # Rule 7: Validate investment_horizon enum
    valid_horizons = {"SHORT_TERM", "MEDIUM_TERM", "LONG_TERM"}
    if data.get("investment_horizon") not in valid_horizons:
        data["investment_horizon"] = "MEDIUM_TERM"

    # Rule 8: Auto-compute total_cost if components are present but total is missing
    fee = data.get("fee_structure", {})
    if fee:
        exp = fee.get("expense_ratio")
        load = fee.get("front_end_load")
        if exp is not None and load is not None and fee.get("total_cost") is None:
            data["fee_structure"]["total_cost"] = round(exp + (load / 5), 2)

    # Rule 9: Validate benchmark_comparison enum
    valid_bench = {"outperforming", "in_line", "underperforming"}
    perf = data.get("performance_metrics", {})
    if perf and perf.get("benchmark_comparison") not in valid_bench:
        data["performance_metrics"]["benchmark_comparison"] = "in_line"

    # Rule 10: EQUITY fund with risk=LOW → upgrade to MEDIUM
    if fund_type == "EQUITY" and data.get("risk_level") == "LOW":
        data["risk_level"] = "MEDIUM"

    return data


async def run_fund_analysis(
    fund_info: FundInfoData,
    nav_history: FundNavHistory,
    performance: FundPerformanceData,
    composition: FundCompositionData,
    checklist: dict | None,
    api_key: str,
    model: str,
) -> FundAnalysisResponse:
    """Call Claude API for fund analysis and return validated response."""
    client_ai = anthropic.AsyncAnthropic(api_key=api_key)
    user_prompt = _build_fund_user_prompt(fund_info, nav_history, performance, composition, checklist or {})

    message = await client_ai.messages.create(
        model=model,
        max_tokens=1024,
        system=FUND_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw_text = message.content[0].text.strip()

    # Extract JSON (handles markdown wrappers)
    json_match = re.search(r"\{[\s\S]*\}", raw_text)
    if not json_match:
        raise ValueError("Claude did not return valid JSON")

    data = json.loads(json_match.group())
    data = _validate_fund_response(data)
    data["current_nav"] = nav_history.current_nav

    return FundAnalysisResponse(**data)
