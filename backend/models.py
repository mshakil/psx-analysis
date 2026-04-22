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
    sma20: float
    sma60: float
    sma120: Optional[float]
    disclaimer: str
    cached_at: str
