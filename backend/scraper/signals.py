import asyncio
import statistics
from datetime import datetime
from typing import Optional
import yfinance as yf
from models import OHLCVBar, SignalBadge, EntryExitLevels, SignalsResponse


def _sync_fetch_yfinance(ticker_ka: str) -> list[dict]:
    """Fetch OHLCV data from yfinance for PSX ticker. Synchronous helper for asyncio.to_thread."""
    try:
        df = yf.download(ticker_ka, period="1y", interval="1d", auto_adjust=True, progress=False)
        if df.empty:
            raise ValueError(f"No data returned from yfinance for {ticker_ka}")
        df = df.reset_index()
        result = []
        for _, row in df.iterrows():
            result.append({
                "date": row["Date"].strftime("%Y-%m-%d"),
                "open": round(float(row["Open"]), 2),
                "high": round(float(row["High"]), 2),
                "low": round(float(row["Low"]), 2),
                "close": round(float(row["Close"]), 2),
                "volume": int(row["Volume"]),
            })
        return result
    except Exception as e:
        raise ValueError(f"yfinance fetch failed for {ticker_ka}: {str(e)}")


async def fetch_ohlcv_yfinance(ticker: str) -> list[OHLCVBar]:
    """Fetch OHLCV data from yfinance asynchronously. Ticker is appended with .KA suffix."""
    ticker_ka = f"{ticker.upper()}.KA"
    ohlcv_dicts = await asyncio.to_thread(_sync_fetch_yfinance, ticker_ka)
    return [OHLCVBar(**d) for d in ohlcv_dicts]


def compute_moving_averages(closes: list[float]) -> dict:
    """Compute 20, 60, 120-day simple moving averages."""
    result = {}
    if len(closes) >= 20:
        result["sma20"] = round(sum(closes[-20:]) / 20, 2)
    else:
        result["sma20"] = None

    if len(closes) >= 60:
        result["sma60"] = round(sum(closes[-60:]) / 60, 2)
    else:
        result["sma60"] = None

    if len(closes) >= 120:
        result["sma120"] = round(sum(closes[-120:]) / 120, 2)
    else:
        result["sma120"] = None

    return result


def compute_volatility(closes: list[float]) -> dict:
    """Compute daily volatility from last 20 closing prices."""
    if len(closes) < 20:
        return {"daily_volatility_pct": None, "label": "INSUFFICIENT_DATA"}

    returns = []
    for i in range(len(closes) - 20, len(closes)):
        if i > 0:
            ret = (closes[i] - closes[i - 1]) / closes[i - 1]
            returns.append(ret)

    if not returns:
        return {"daily_volatility_pct": None, "label": "INSUFFICIENT_DATA"}

    daily_vol = statistics.stdev(returns) if len(returns) > 1 else 0
    daily_vol_pct = daily_vol * 100

    if daily_vol_pct >= 2.0:
        label = "HIGH"
    elif daily_vol_pct <= 1.0:
        label = "LOW"
    else:
        label = "MODERATE"

    return {"daily_volatility_pct": round(daily_vol_pct, 2), "label": label}


def compute_volume_signal(volumes: list[float], current_volume: float) -> dict:
    """Compare current volume to 30-day average."""
    if len(volumes) < 30:
        return {"ratio": None, "label": "INSUFFICIENT_DATA"}

    avg_30d = sum(volumes[-30:]) / 30
    if avg_30d == 0:
        ratio = 0
    else:
        ratio = current_volume / avg_30d

    if ratio >= 1.5:
        label = "SPIKE"
    elif ratio <= 0.7:
        label = "DRY"
    else:
        label = "NORMAL"

    return {"ratio": round(ratio, 2), "label": label}


def compute_trend_signal(sma20: Optional[float], sma60: Optional[float], sma120: Optional[float], current_price: float) -> dict:
    """Determine trend from three-MA alignment."""
    if not sma20 or not sma60:
        return {"direction": "UNKNOWN", "label": "Insufficient data"}

    if sma120:
        if sma20 > sma60 and sma60 > sma120:
            return {"direction": "UPTREND", "label": "Clear upward trend"}
        elif sma20 < sma60 and sma60 < sma120:
            return {"direction": "DOWNTREND", "label": "Downward pressure on price"}
        else:
            max_sma = max(sma20, sma60, sma120)
            min_sma = min(sma20, sma60, sma120)
            if max_sma / min_sma < 1.05:
                return {"direction": "SIDEWAYS", "label": "No clear direction"}
            else:
                return {"direction": "SIDEWAYS", "label": "No clear direction"}
    else:
        if abs(sma20 - sma60) / sma60 < 0.03:
            return {"direction": "SIDEWAYS", "label": "No clear direction"}
        elif sma20 > sma60:
            return {"direction": "UPTREND", "label": "Clear upward trend"}
        else:
            return {"direction": "DOWNTREND", "label": "Downward pressure on price"}


def find_support_resistance(highs: list[float], lows: list[float], current_price: float) -> dict:
    """Find support and resistance levels using cluster method (3+ touches within 5%)."""
    support = None
    resistance = None
    near_support = False
    near_resistance = False

    if len(lows) >= 10:
        unique_lows = sorted(set([round(l, 0) for l in lows[-60:]]))
        support_candidates = []
        for level in unique_lows:
            if level > 0:
                touches = sum(1 for l in lows[-60:] if abs(l - level) / level <= 0.05)
                if touches >= 3 and level < current_price:
                    support_candidates.append(level)
        if support_candidates:
            support = max(support_candidates)
            near_support = (current_price - support) / support <= 0.03

    if len(highs) >= 10:
        unique_highs = sorted(set([round(h, 0) for h in highs[-60:]]))
        resistance_candidates = []
        for level in unique_highs:
            if level > 0:
                touches = sum(1 for h in highs[-60:] if abs(h - level) / level <= 0.05)
                if touches >= 3 and level > current_price:
                    resistance_candidates.append(level)
        if resistance_candidates:
            resistance = min(resistance_candidates)
            near_resistance = (resistance - current_price) / current_price <= 0.03

    return {
        "support": round(support, 2) if support else None,
        "resistance": round(resistance, 2) if resistance else None,
        "near_support": near_support,
        "near_resistance": near_resistance,
    }


def compute_momentum_signal(closes: list[float], sma20: Optional[float], sma60: Optional[float]) -> dict:
    """3-check momentum system: MA align, price above SMA20, short-term acceleration."""
    if not sma20 or not sma60 or len(closes) < 20:
        return {"bullish_checks": 0, "bearish_checks": 0, "label": "WEAK"}

    current_price = closes[-1]
    check1 = sma20 > sma60
    check2 = current_price > sma20
    check3 = (sum(closes[-5:]) / 5) > (sum(closes[-15:-5]) / 10)

    bullish_count = sum([check1, check2, check3])
    bearish_count = 3 - bullish_count

    if bullish_count == 3:
        label = "STRONG"
    elif bullish_count == 2:
        label = "MODERATE"
    elif bullish_count == 1:
        label = "WEAK"
    else:
        label = "FADING"

    return {"bullish_checks": bullish_count, "bearish_checks": bearish_count, "label": label}


def compute_entry_exit(current_price: float, support: Optional[float], resistance: Optional[float], week_52_high: float, week_52_low: float, volatility_pct: float) -> dict:
    """Compute entry, stop loss, and target prices."""
    entry_low = (support * 0.99) if support else (current_price * 0.99)
    entry_high = (support * 1.01) if support else (current_price * 1.01)

    stop_loss = max((support * 0.95) if support else (current_price * 0.90), current_price * 0.90)

    target1 = resistance if (resistance and resistance > current_price * 1.02) else (current_price * 1.08)
    target2 = week_52_high if (week_52_high > current_price * 1.05) else (current_price * 1.15)

    if stop_loss > 0:
        risk_reward = round((target1 - current_price) / (current_price - stop_loss), 1)
    else:
        risk_reward = 0

    entry_label = "Buy near support" if support else "Monitor for entry"
    stop_label = f"Protective stop: PKR {round(stop_loss, 2)}"
    target1_label = f"First target: PKR {round(target1, 2)}"
    target2_label = f"Extended target: PKR {round(target2, 2)}"

    return {
        "entry_low": round(entry_low, 2),
        "entry_high": round(entry_high, 2),
        "stop_loss": round(stop_loss, 2),
        "target1": round(target1, 2),
        "target2": round(target2, 2),
        "risk_reward_ratio": risk_reward,
        "entry_label": entry_label,
        "stop_label": stop_label,
        "target1_label": target1_label,
        "target2_label": target2_label,
    }


def build_signals(ohlcv: list[OHLCVBar], current_volume: float, week_52_high: float, week_52_low: float) -> dict:
    """Orchestrate all signal calculations."""
    if not ohlcv:
        raise ValueError("Empty OHLCV data")

    closes = [bar.close for bar in ohlcv]
    highs = [bar.high for bar in ohlcv]
    lows = [bar.low for bar in ohlcv]
    volumes = [bar.volume for bar in ohlcv]
    current_price = closes[-1]

    mas = compute_moving_averages(closes)
    volatility = compute_volatility(closes)
    volume_signal = compute_volume_signal(volumes, current_volume)
    trend = compute_trend_signal(mas.get("sma20"), mas.get("sma60"), mas.get("sma120"), current_price)
    sr = find_support_resistance(highs, lows, current_price)
    momentum = compute_momentum_signal(closes, mas.get("sma20"), mas.get("sma60"))
    entry_exit = compute_entry_exit(current_price, sr.get("support"), sr.get("resistance"), week_52_high, week_52_low, volatility.get("daily_volatility_pct", 0))

    return {
        "sma20": mas.get("sma20"),
        "sma60": mas.get("sma60"),
        "sma120": mas.get("sma120"),
        "volatility": volatility,
        "volume_signal": volume_signal,
        "trend": trend,
        "support_resistance": sr,
        "momentum": momentum,
        "entry_exit": entry_exit,
        "current_price": current_price,
    }


def translate_signals_to_plain_english(signals: dict) -> list[SignalBadge]:
    """Convert internal signal codes to plain-English UI badges."""
    badges = []

    trend = signals["trend"]
    if trend["direction"] == "UPTREND":
        badges.append(SignalBadge(text="Clear upward trend", sentiment="BULLISH", category="trend"))
    elif trend["direction"] == "DOWNTREND":
        badges.append(SignalBadge(text="Downward pressure on price", sentiment="BEARISH", category="trend"))

    momentum = signals["momentum"]
    if momentum["label"] == "STRONG":
        badges.append(SignalBadge(text="Strong buying momentum", sentiment="BULLISH", category="momentum"))
    elif momentum["label"] == "MODERATE":
        badges.append(SignalBadge(text="Moderate buying pressure", sentiment="BULLISH", category="momentum"))
    elif momentum["label"] == "WEAK":
        badges.append(SignalBadge(text="Weak momentum — cautious", sentiment="NEUTRAL", category="momentum"))
    elif momentum["label"] == "FADING":
        badges.append(SignalBadge(text="Buyers losing interest", sentiment="BEARISH", category="momentum"))

    volume_sig = signals["volume_signal"]
    if volume_sig["label"] == "SPIKE":
        badges.append(SignalBadge(text="Heavy trading interest today", sentiment="BULLISH", category="volume"))
    elif volume_sig["label"] == "DRY":
        badges.append(SignalBadge(text="Low trader participation", sentiment="BEARISH", category="volume"))

    volatility = signals["volatility"]
    if volatility["label"] == "HIGH":
        badges.append(SignalBadge(text="Wide price swings — higher risk", sentiment="NEUTRAL", category="volatility"))
    elif volatility["label"] == "LOW":
        badges.append(SignalBadge(text="Calm price movement", sentiment="NEUTRAL", category="volatility"))

    sr = signals["support_resistance"]
    if sr["near_support"]:
        badges.append(SignalBadge(text="Price near support zone", sentiment="BULLISH", category="support_resistance"))
    if sr["near_resistance"]:
        badges.append(SignalBadge(text="Price approaching resistance", sentiment="BEARISH", category="support_resistance"))

    return badges
