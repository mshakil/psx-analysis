from pydantic import BaseModel, Field
from typing import Literal, Optional
from enum import Enum


class Verdict(str, Enum):
    BUY_NOW = "BUY NOW"
    BUY_SLOWLY = "BUY SLOWLY"
    HOLD = "HOLD"
    STAY_AWAY = "STAY AWAY"
    SELL = "SELL"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class LiquidityStatus(str, Enum):
    STRONG = "STRONG"
    MODERATE = "MODERATE"
    WEAK = "WEAK"


class DataQuality(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ChecklistTask(BaseModel):
    name: str
    status: Literal["DONE", "FAILED", "PENDING"]
    detail: Optional[str] = None


class AnalysisRequest(BaseModel):
    ticker: str = Field(..., min_length=2, max_length=10)
    checklist: Optional[dict] = None


class MarketData(BaseModel):
    ticker: str
    company_name: str
    sector: str
    current_price: float
    open_price: float
    price_change_pct: float
    avg_volume_30d: float
    current_volume: float
    week_52_high: float
    week_52_low: float
    price_vs_52w_high_pct: float
    trend_direction: str
    recent_prices: list[dict]


class NewsData(BaseModel):
    company_headlines: list[str]
    macro_headlines: list[str]
    sentiment_hint: str


class FinancialsData(BaseModel):
    pe_ratio: Optional[float] = None
    dividend_yield: Optional[float] = None
    market_cap_bn_pkr: Optional[float] = None
    data_available: bool


class AnalysisResponse(BaseModel):
    ticker: str
    verdict: Verdict
    confidence_score: int = Field(..., ge=0, le=100)
    risk_level: RiskLevel
    liquidity_status: LiquidityStatus
    summary_plain_english: str = Field(..., max_length=800)
    bull_case: list[str]
    bear_case: list[str]
    key_drivers: list[str]
    data_quality: DataQuality
    checklist: dict
    recent_prices: list[dict]
    current_price: float


class OHLCVBar(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float


class SignalBadge(BaseModel):
    text: str
    sentiment: Literal["BULLISH", "BEARISH", "NEUTRAL"]
    category: Literal["momentum", "volatility", "volume", "trend", "support_resistance"]


class EntryExitLevels(BaseModel):
    entry_low: float
    entry_high: float
    stop_loss: float
    target1: float
    target2: float
    risk_reward_ratio: float
    entry_label: str
    stop_label: str
    target1_label: str
    target2_label: str


class SignalsResponse(BaseModel):
    ticker: str
    timeframe_days: int
    ohlcv: list[OHLCVBar]
    badges: list[SignalBadge]
    entry_exit: EntryExitLevels
    support_level: Optional[float]
    resistance_level: Optional[float]
    sma20: Optional[float]
    sma60: Optional[float]
    sma120: Optional[float]
    disclaimer: str
    cached_at: str


# ============================================
# PHASE 3: MUTUAL FUND ANALYSIS MODELS
# ============================================

class FundType(str, Enum):
    EQUITY = "EQUITY"
    FIXED_INCOME = "FIXED_INCOME"
    BALANCED = "BALANCED"
    INDEX = "INDEX"
    VPS = "VPS"
    OTHER = "OTHER"


class InvestmentHorizon(str, Enum):
    SHORT_TERM = "SHORT_TERM"
    MEDIUM_TERM = "MEDIUM_TERM"
    LONG_TERM = "LONG_TERM"


class BenchmarkComparison(str, Enum):
    OUTPERFORMING = "outperforming"
    IN_LINE = "in_line"
    UNDERPERFORMING = "underperforming"


class FeeAssessment(str, Enum):
    EXPENSIVE = "expensive"
    FAIR = "fair"
    CHEAP = "cheap"


# --- Scraper data models (soft-fail with data_available flag) ---


class NAVBar(BaseModel):
    date: str
    nav: float


class FundNavHistory(BaseModel):
    fund_code: str
    nav_bars: list[NAVBar]
    current_nav: Optional[float] = None
    nav_1w_change_pct: Optional[float] = None
    nav_1m_change_pct: Optional[float] = None
    data_available: bool


class FundPerformanceData(BaseModel):
    returns_1y: Optional[float] = None
    returns_3y: Optional[float] = None
    returns_5y: Optional[float] = None
    benchmark_returns_1y: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    std_deviation: Optional[float] = None
    beta: Optional[float] = None
    data_available: bool


class FundCompositionData(BaseModel):
    top_holdings: list[str] = []
    sector_allocation: dict[str, float] = {}
    asset_mix: dict[str, float] = {}
    data_available: bool


class FundInfoData(BaseModel):
    fund_code: str
    fund_name: str
    fund_type: str
    amc_name: str
    current_nav: Optional[float] = None
    aum_bn_pkr: Optional[float] = None
    expense_ratio: Optional[float] = None
    front_end_load: Optional[float] = None
    manager_name: Optional[str] = None
    manager_tenure_years: Optional[float] = None
    inception_date: Optional[str] = None
    data_available: bool


# --- Request/Response models ---


class FundAnalysisRequest(BaseModel):
    fund_code: str = Field(..., min_length=2, max_length=30)
    checklist: Optional[dict] = None


class FundListItem(BaseModel):
    fund_code: str
    fund_name: str
    fund_type: str
    amc_name: str
    current_nav: Optional[float] = None
    ytd_return: Optional[float] = None


class PerformanceMetrics(BaseModel):
    returns_1y: Optional[float] = None
    returns_3y: Optional[float] = None
    returns_5y: Optional[float] = None
    benchmark_comparison: Optional[BenchmarkComparison] = None
    sharpe_ratio: Optional[float] = None
    volatility: Optional[str] = None
    beta: Optional[float] = None


class FeeStructure(BaseModel):
    expense_ratio: Optional[float] = None
    front_end_load: Optional[float] = None
    total_cost: Optional[float] = None
    fee_assessment: Optional[FeeAssessment] = None


class CompositionBreakdown(BaseModel):
    top_holdings: list[str] = []
    sector_allocation: dict[str, float] = {}
    asset_mix: dict[str, float] = {}


class FundAnalysisResponse(BaseModel):
    fund_code: str
    fund_name: str
    fund_type: FundType
    verdict: Verdict
    confidence_score: int = Field(..., ge=0, le=100)
    risk_level: RiskLevel
    investment_horizon: InvestmentHorizon
    summary_plain_english: str = Field(..., max_length=800)
    manager_assessment: str
    cost_benefit_analysis: str
    composition_breakdown: CompositionBreakdown
    performance_metrics: PerformanceMetrics
    fee_structure: FeeStructure
    bull_case: list[str]
    bear_case: list[str]
    key_drivers: list[str]
    data_quality: DataQuality
    checklist: dict
    current_nav: Optional[float] = None


class FundComparisonSummary(BaseModel):
    better_returns: Optional[str] = None
    lower_fees: Optional[str] = None
    best_risk_adjusted: Optional[str] = None
    overall_winner: Optional[str] = None


class FundComparisonResponse(BaseModel):
    funds: list[FundAnalysisResponse]
    comparison: FundComparisonSummary


class FundSignalsResponse(BaseModel):
    fund_code: str
    timeframe_days: int
    nav_history: list[NAVBar]
    badges: list[SignalBadge]
    trend_direction: str
    sma20: Optional[float] = None
    sma60: Optional[float] = None
    sma120: Optional[float] = None
    disclaimer: str
    cached_at: str
