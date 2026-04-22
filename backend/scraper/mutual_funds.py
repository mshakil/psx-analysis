"""
MUFAP (Pakistan Mutual Funds Association) data scraper.
Fetches fund list, NAV history, performance, composition, and manager info.

All functions follow soft-fail pattern: return Model(data_available=False) on any Exception.
Never raise — graceful fallback for missing data.
"""

import asyncio
import re
import httpx
from datetime import datetime, timedelta
from typing import Optional
from bs4 import BeautifulSoup
from models import (
    FundNavHistory,
    FundPerformanceData,
    FundCompositionData,
    FundInfoData,
    NAVBar,
    FundType,
)


# Module-level cache for fund list (populated at startup)
_FUND_CACHE: dict[str, dict] = {}

# MUFAP URLs
MUFAP_BASE = "https://www.mufap.com.pk"
MUFAP_NAV_LIST = f"{MUFAP_BASE}/nav_returns_data.php"
MUFAP_PROFILE = f"{MUFAP_BASE}/fund_profile.php"
MUFAP_PERF = f"{MUFAP_BASE}/fund_performance.php"


def _safe_float(text: str) -> Optional[float]:
    """Extract float from text containing numbers, %, commas, and units. Returns None if parse fails."""
    if not text:
        return None
    cleaned = re.sub(r"[^\d.]", "", str(text).strip())
    try:
        return float(cleaned) if cleaned else None
    except ValueError:
        return None


def _parse_fund_type(raw_type: str) -> str:
    """Map MUFAP fund type text to our FundType enum values."""
    if not raw_type:
        return FundType.OTHER.value

    raw = raw_type.lower().strip()
    if "equity" in raw or "growth" in raw or "stock" in raw:
        return FundType.EQUITY.value
    elif "income" in raw or "fixed" in raw or "bond" in raw or "debt" in raw:
        return FundType.FIXED_INCOME.value
    elif "balance" in raw or "asset" in raw or "alloc" in raw:
        return FundType.BALANCED.value
    elif "index" in raw or "passive" in raw:
        return FundType.INDEX.value
    elif "vps" in raw or "pension" in raw:
        return FundType.VPS.value
    else:
        return FundType.OTHER.value


def _parse_nav_table(soup: BeautifulSoup, limit: int = 252) -> list[dict]:
    """
    Parse NAV history table from MUFAP page.
    Returns list of {date, nav} dicts (oldest first).
    """
    nav_bars = []
    try:
        # Find NAV table (typically has class "table" or similar)
        tables = soup.find_all("table")
        for table in tables:
            rows = table.find_all("tr")[1:]  # Skip header
            for row in rows[:limit]:
                cols = row.find_all("td")
                if len(cols) >= 2:
                    date_str = cols[0].text.strip()
                    nav_str = cols[1].text.strip()
                    nav = _safe_float(nav_str)
                    if nav is not None:
                        nav_bars.append({"date": date_str, "nav": nav})
            if nav_bars:
                break
    except Exception:
        pass

    return list(reversed(nav_bars))  # Return oldest-first


def _parse_holdings_table(soup: BeautifulSoup, limit: int = 10) -> list[str]:
    """Extract top N holdings from fund profile page. Returns list of holding names."""
    holdings = []
    try:
        # Find holdings table or section
        tables = soup.find_all("table")
        for table in tables:
            rows = table.find_all("tr")[1:]  # Skip header
            for row in rows[:limit]:
                cols = row.find_all("td")
                if cols:
                    holding_name = cols[0].text.strip()
                    if holding_name:
                        holdings.append(holding_name)
            if holdings:
                break
    except Exception:
        pass

    return holdings


def _parse_sector_allocation(soup: BeautifulSoup) -> dict[str, float]:
    """Extract sector allocation from profile page. Returns {sector: percentage}."""
    allocation = {}
    try:
        # Look for sector allocation table/list
        tables = soup.find_all("table")
        for table in tables:
            # Check if this looks like a sector table (has "sector" in context)
            table_text = table.text.lower()
            if "sector" in table_text or "allocation" in table_text:
                rows = table.find_all("tr")[1:]  # Skip header
                for row in rows:
                    cols = row.find_all("td")
                    if len(cols) >= 2:
                        sector = cols[0].text.strip()
                        pct = _safe_float(cols[1].text.strip())
                        if sector and pct is not None:
                            allocation[sector] = pct
                if allocation:
                    break
    except Exception:
        pass

    return allocation


async def load_fund_cache(client: httpx.AsyncClient) -> None:
    """
    Called at FastAPI startup. Fetches and caches complete MUFAP fund list.
    Populates _FUND_CACHE with all available funds.
    Never raises — logs warning and continues if MUFAP unreachable.
    """
    global _FUND_CACHE
    try:
        # Fetch NAV list page with all funds
        resp = await client.get(
            MUFAP_NAV_LIST,
            params={"tab": "daily_return"},
            timeout=15.0,
            headers={"User-Agent": "Mozilla/5.0 (IntelliTrade/1.0)"},
        )
        if resp.status_code != 200:
            print(f"⚠️  MUFAP fund list returned {resp.status_code}, cache empty")
            return

        soup = BeautifulSoup(resp.text, "lxml")
        tables = soup.find_all("table")

        fund_count = 0
        for table in tables:
            rows = table.find_all("tr")[1:]  # Skip header
            for row in rows:
                cols = row.find_all("td")
                if len(cols) >= 5:
                    try:
                        # Parse row: name, amc, type, nav, ytd_return
                        fund_code = cols[0].text.strip()
                        fund_name = cols[0].text.strip()  # Usually same as code or link text
                        amc_name = cols[1].text.strip()
                        fund_type_str = cols[2].text.strip()
                        current_nav = _safe_float(cols[3].text.strip())
                        ytd_return = _safe_float(cols[4].text.strip())

                        fund_type = _parse_fund_type(fund_type_str)

                        if fund_code:
                            _FUND_CACHE[fund_code.upper()] = {
                                "fund_code": fund_code.upper(),
                                "fund_name": fund_name,
                                "amc_name": amc_name,
                                "fund_type": fund_type,
                                "current_nav": current_nav,
                                "ytd_return": ytd_return,
                            }
                            fund_count += 1
                    except Exception:
                        continue

        print(f"✅ Loaded {fund_count} MUFAP funds to cache")
        return

    except Exception as e:
        print(f"⚠️  MUFAP load_fund_cache failed: {str(e)}")
        return


def validate_fund_code(fund_code: str) -> tuple[bool, str, str]:
    """
    Validate fund exists in _FUND_CACHE.
    Returns (is_valid, fund_name, fund_type).
    Mirrors validate_ticker() pattern exactly.
    """
    code = fund_code.upper() if fund_code else ""
    if code in _FUND_CACHE:
        fund = _FUND_CACHE[code]
        return (True, fund["fund_name"], fund["fund_type"])
    return (False, "", "")


def search_funds(query: str, limit: int = 20) -> list[dict]:
    """
    In-memory substring search over _FUND_CACHE by code or name.
    Returns list of matching funds (max `limit` results).
    Case-insensitive.
    """
    query_lower = query.lower()
    results = []

    for code, fund in _FUND_CACHE.items():
        if (query_lower in code.lower() or
            query_lower in fund["fund_name"].lower() or
            query_lower in fund["amc_name"].lower()):
            results.append(fund)
            if len(results) >= limit:
                break

    return results


async def fetch_fund_info(fund_code: str, client: httpx.AsyncClient) -> FundInfoData:
    """
    Fetch fund profile page (expense ratio, front-end load, manager, AUM, inception).
    Returns FundInfoData(data_available=False) on any Exception.
    """
    try:
        code = fund_code.upper()
        resp = await client.get(
            MUFAP_PROFILE,
            params={"fund_code": code},
            timeout=10.0,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        if resp.status_code != 200:
            return FundInfoData(fund_code=code, fund_name="", fund_type="", amc_name="", data_available=False)

        soup = BeautifulSoup(resp.text, "lxml")

        # Extract info using label-value pattern (similar to financials.py)
        fund_name = soup.find("h1")
        fund_name_text = fund_name.text.strip() if fund_name else ""

        def find_stat(label_text: str) -> Optional[str]:
            """Find a stat by label text, return adjacent value."""
            try:
                labels = soup.find_all(string=re.compile(label_text, re.I))
                if labels:
                    parent = labels[0].parent
                    value_tag = parent.find_next_sibling()
                    return value_tag.text.strip() if value_tag else None
            except Exception:
                pass
            return None

        # Parse values
        expense_ratio = _safe_float(find_stat("Expense Ratio") or "")
        front_end_load = _safe_float(find_stat("Front-End Load") or "")
        manager_name = find_stat("Fund Manager") or None
        manager_tenure = _safe_float(find_stat("Manager Tenure") or "")
        aum = _safe_float(find_stat("Total Assets|AUM") or "")
        inception = find_stat("Inception Date") or None

        # Try to get fund type and AMC from cache if available
        cache_fund = _FUND_CACHE.get(code, {})
        fund_type = cache_fund.get("fund_type", "OTHER")
        amc_name = cache_fund.get("amc_name", "")
        current_nav = _safe_float(find_stat("Current NAV") or "")

        data_available = (expense_ratio is not None or front_end_load is not None or
                         manager_name is not None or aum is not None)

        return FundInfoData(
            fund_code=code,
            fund_name=fund_name_text or cache_fund.get("fund_name", ""),
            fund_type=fund_type,
            amc_name=amc_name,
            current_nav=current_nav,
            aum_bn_pkr=aum,
            expense_ratio=expense_ratio,
            front_end_load=front_end_load,
            manager_name=manager_name,
            manager_tenure_years=manager_tenure,
            inception_date=inception,
            data_available=data_available,
        )

    except Exception:
        return FundInfoData(fund_code=fund_code.upper(), fund_name="", fund_type="", amc_name="", data_available=False)


async def fetch_fund_nav_history(
    fund_code: str, client: httpx.AsyncClient, length: int = 252
) -> FundNavHistory:
    """
    Fetch NAV history table from MUFAP. Returns FundNavHistory(data_available=False) on Exception.
    Computes 1w/1m change percentages for trend detection.
    """
    try:
        code = fund_code.upper()
        resp = await client.get(
            MUFAP_NAV_LIST,
            params={"tab": "nav_history", "fund_code": code},
            timeout=10.0,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        if resp.status_code != 200:
            return FundNavHistory(fund_code=code, nav_bars=[], data_available=False)

        soup = BeautifulSoup(resp.text, "lxml")
        nav_bars = _parse_nav_table(soup, limit=length)

        if not nav_bars:
            return FundNavHistory(fund_code=code, nav_bars=[], data_available=False)

        # Convert to NAVBar objects
        nav_bar_objs = [NAVBar(date=bar["date"], nav=bar["nav"]) for bar in nav_bars]

        # Calculate current NAV and changes
        current_nav = nav_bars[-1]["nav"] if nav_bars else None
        nav_1w_ago = nav_bars[-8]["nav"] if len(nav_bars) > 7 else None
        nav_1m_ago = nav_bars[-21]["nav"] if len(nav_bars) > 20 else None

        nav_1w_change = None
        nav_1m_change = None
        if current_nav and nav_1w_ago:
            nav_1w_change = ((current_nav - nav_1w_ago) / nav_1w_ago) * 100
        if current_nav and nav_1m_ago:
            nav_1m_change = ((current_nav - nav_1m_ago) / nav_1m_ago) * 100

        return FundNavHistory(
            fund_code=code,
            nav_bars=nav_bar_objs,
            current_nav=current_nav,
            nav_1w_change_pct=nav_1w_change,
            nav_1m_change_pct=nav_1m_change,
            data_available=True,
        )

    except Exception:
        return FundNavHistory(fund_code=fund_code.upper(), nav_bars=[], data_available=False)


async def fetch_fund_performance(fund_code: str, client: httpx.AsyncClient) -> FundPerformanceData:
    """
    Fetch 1Y/3Y/5Y returns and benchmark comparison from performance page.
    Returns FundPerformanceData(data_available=False) on Exception.
    """
    try:
        code = fund_code.upper()
        resp = await client.get(
            MUFAP_PERF,
            params={"fund_code": code},
            timeout=10.0,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        if resp.status_code != 200:
            return FundPerformanceData(data_available=False)

        soup = BeautifulSoup(resp.text, "lxml")

        def find_stat(label_text: str) -> Optional[str]:
            """Find a stat by label text, return adjacent value."""
            try:
                labels = soup.find_all(string=re.compile(label_text, re.I))
                if labels:
                    parent = labels[0].parent
                    value_tag = parent.find_next_sibling()
                    return value_tag.text.strip() if value_tag else None
            except Exception:
                pass
            return None

        returns_1y = _safe_float(find_stat("1-Year Return") or "")
        returns_3y = _safe_float(find_stat("3-Year Return") or "")
        returns_5y = _safe_float(find_stat("5-Year Return") or "")
        benchmark_1y = _safe_float(find_stat("Benchmark.*1.*Year") or "")
        sharpe = _safe_float(find_stat("Sharpe Ratio") or "")
        std_dev = _safe_float(find_stat("Standard Deviation|Volatility") or "")
        beta = _safe_float(find_stat("Beta") or "")

        data_available = (returns_1y is not None or returns_3y is not None or
                         returns_5y is not None or sharpe is not None)

        return FundPerformanceData(
            returns_1y=returns_1y,
            returns_3y=returns_3y,
            returns_5y=returns_5y,
            benchmark_returns_1y=benchmark_1y,
            sharpe_ratio=sharpe,
            std_deviation=std_dev,
            beta=beta,
            data_available=data_available,
        )

    except Exception:
        return FundPerformanceData(data_available=False)


async def fetch_fund_composition(fund_code: str, client: httpx.AsyncClient) -> FundCompositionData:
    """
    Fetch fund composition (top 10 holdings, sector allocation, asset mix).
    Returns FundCompositionData(data_available=False) on Exception.
    """
    try:
        code = fund_code.upper()
        resp = await client.get(
            MUFAP_PROFILE,
            params={"fund_code": code},
            timeout=10.0,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        if resp.status_code != 200:
            return FundCompositionData(data_available=False)

        soup = BeautifulSoup(resp.text, "lxml")

        top_holdings = _parse_holdings_table(soup, limit=10)
        sector_allocation = _parse_sector_allocation(soup)

        # Try to find asset mix (stocks%, bonds%, cash%)
        asset_mix = {}
        try:
            labels = soup.find_all(string=re.compile("Stocks|Bonds|Cash", re.I))
            for label in labels:
                parent = label.parent
                value_tag = parent.find_next_sibling()
                if value_tag:
                    pct = _safe_float(value_tag.text.strip())
                    if pct is not None:
                        asset_type = label.text.strip()
                        asset_mix[asset_type] = pct
        except Exception:
            pass

        data_available = len(top_holdings) > 0 or len(sector_allocation) > 0 or len(asset_mix) > 0

        return FundCompositionData(
            top_holdings=top_holdings,
            sector_allocation=sector_allocation,
            asset_mix=asset_mix,
            data_available=data_available,
        )

    except Exception:
        return FundCompositionData(data_available=False)
