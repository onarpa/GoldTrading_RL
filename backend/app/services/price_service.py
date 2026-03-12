"""
Price Service
=============
1. Seed historical data จาก CSV ตอน startup (ครั้งแรก)
2. ดึง XAU/USD hourly  → Twelve Data API   (free: 800 credits/day)
3. ดึง WTI oil daily   → Twelve Data API   (symbol=WTI, interval=1day)
4. คำนวณ technical indicators (EMA50, EMA200, RSI, MACD)

API Sources:
  Gold : https://api.twelvedata.com/time_series?symbol=XAU/USD&interval=1h
  Oil  : https://api.twelvedata.com/time_series?symbol=WTI&interval=1day
"""
import httpx
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
from sqlmodel import Session
from typing import Optional
import logging
import os

from app.core.config import get_settings
from database.models import GoldPrice, OilPrice
from database import crud

logger   = logging.getLogger(__name__)
settings = get_settings()
now_utc = datetime.now(timezone.utc)

TWELVE_DATA_BASE = "https://api.twelvedata.com"


# ---------------------------------------------------------------------------
# Seed data from CSV (รันครั้งเดียวตอน startup)
# ---------------------------------------------------------------------------

async def seed_gold_from_api(session: Session) -> int:
    """
    Seed 500 bars ล่าสุดจาก Twelve Data API (1 credit เท่านั้น)
    เรียกตอน startup ถ้า DB ยังไม่มีข้อมูล
    """
    if len(crud.get_latest_gold_prices(session, limit=1)) > 0:
        logger.info("Gold price data already exists — skipping API seed")
        return 0

    key = settings.twelve_data_api_key
    if not key or key in ("demo", ""):
        logger.info("No API key — falling back to CSV seed")
        return seed_gold_from_csv(session)

    logger.info("Seeding 500 bars from Twelve Data API ...")
    params = {
        "symbol":     "XAU/USD",
        "interval":   "1h",
        "outputsize": "5000",
        "apikey":     key,
        "format":     "JSON",
        "timezone":   "UTC",
    }
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(f"{TWELVE_DATA_BASE}/time_series", params=params)
            resp.raise_for_status()
        raw = resp.json()
        if raw.get("status") == "error":
            logger.warning(f"Twelve Data error: {raw.get('message')} — falling back to CSV")
            return seed_gold_from_csv(session)
    except Exception as e:
        logger.error(f"API seed failed: {e} — falling back to CSV")
        return seed_gold_from_csv(session)

    df = _parse_twelve_data_df(raw)
    if df.empty:
        return seed_gold_from_csv(session)

    closes = df["close"].values.astype(np.float64)
    ema50  = _ema(closes, 50)
    ema200 = _ema(closes, 200)
    rsi14  = _rsi(closes, 14)
    macd_l, macd_s, macd_h = _macd(closes, 12, 26, 9)
    bb_u, bb_m, bb_l = _bollinger(closes, 20, 2.0)

    for i, row in df.iterrows():
        crud.upsert_gold_price(session, GoldPrice(
            timestamp   = row["timestamp"].to_pydatetime(),
            open        = float(row["open"]),
            high        = float(row["high"]),
            low         = float(row["low"]),
            close       = float(row["close"]),
            volume      = float(row["volume"]),
            ema_50      = float(ema50[i])  if not np.isnan(ema50[i])  else None,
            ema_200     = float(ema200[i]) if not np.isnan(ema200[i]) else None,
            rsi         = float(rsi14[i])  if not np.isnan(rsi14[i])  else None,
            macd        = float(macd_l[i]) if not np.isnan(macd_l[i]) else None,
            macd_signal = float(macd_s[i]) if not np.isnan(macd_s[i]) else None,
            macd_hist   = float(macd_h[i]) if not np.isnan(macd_h[i]) else None,
            bb_upper    = float(bb_u[i])   if not np.isnan(bb_u[i])   else None,
            bb_mid      = float(bb_m[i])   if not np.isnan(bb_m[i])   else None,
            bb_lower    = float(bb_l[i])   if not np.isnan(bb_l[i])   else None,
        ))
    session.commit()
    logger.info(f"API seed complete: {len(df)} rows")
    return len(df)


def seed_gold_from_csv(session: Session) -> int:
    csv_path = settings.seed_gold_csv
    if not os.path.exists(csv_path):
        logger.warning(f"Gold seed CSV not found: {csv_path}")
        return 0
    if len(crud.get_latest_gold_prices(session, limit=1)) > 0:
        logger.info("Gold price data already exists — skipping CSV seed")
        return 0

    logger.info(f"Seeding gold prices from {csv_path} ...")
    df = pd.read_csv(csv_path, sep=";")
    df.columns = [c.strip() for c in df.columns]
    df["timestamp"] = pd.to_datetime(df["Date"], format="%Y.%m.%d %H:%M")
    df = df.rename(columns={"Open": "open", "High": "high", "Low": "low",
                             "Close": "close", "Volume": "volume"})
    closes = df["close"].values.astype(np.float64)
    ema50  = _ema(closes, 50)
    ema200 = _ema(closes, 200)
    rsi14  = _rsi(closes, 14)
    macd_l, macd_s, macd_h = _macd(closes, 12, 26, 9)
    bb_u, bb_m, bb_l = _bollinger(closes, 20, 2.0)

    count, batch = 0, []
    for i, row in df.iterrows():
        batch.append(GoldPrice(
            timestamp   = row["timestamp"].to_pydatetime(),
            open        = float(row["open"]),
            high        = float(row["high"]),
            low         = float(row["low"]),
            close       = float(row["close"]),
            volume      = float(row["volume"]),
            ema_50      = float(ema50[i])  if not np.isnan(ema50[i])  else None,
            ema_200     = float(ema200[i]) if not np.isnan(ema200[i]) else None,
            rsi         = float(rsi14[i])  if not np.isnan(rsi14[i])  else None,
            macd        = float(macd_l[i]) if not np.isnan(macd_l[i]) else None,
            macd_signal = float(macd_s[i]) if not np.isnan(macd_s[i]) else None,
            macd_hist   = float(macd_h[i]) if not np.isnan(macd_h[i]) else None,
            bb_upper    = float(bb_u[i])   if not np.isnan(bb_u[i])   else None,
            bb_mid      = float(bb_m[i])   if not np.isnan(bb_m[i])   else None,
            bb_lower    = float(bb_l[i])   if not np.isnan(bb_l[i])   else None,
        ))
        count += 1
        if len(batch) >= 5000:
            for p in batch: session.add(p)
            session.commit(); batch.clear()
            logger.info(f"  Seeded {count} gold rows...")

    if batch:
        for p in batch: session.add(p)
        session.commit()
    logger.info(f"Gold seed complete: {count} rows")
    return count


def seed_oil_from_csv(session: Session) -> int:
    csv_path = settings.seed_oil_csv
    if not os.path.exists(csv_path):
        logger.warning(f"Oil seed CSV not found: {csv_path}")
        return 0
    if crud.get_latest_oil(session) is not None:
        logger.info("Oil price data already exists — skipping CSV seed")
        return 0

    logger.info(f"Seeding oil prices from {csv_path} ...")
    df = pd.read_csv(csv_path)
    df.columns = [c.strip() for c in df.columns]
    df["timestamp"] = pd.to_datetime(df["date"], utc=True).dt.tz_localize(None)
    df = df[["timestamp", "price"]].dropna().sort_values("timestamp").reset_index(drop=True)

    count = 0
    for i, row in df.iterrows():
        ts, price = row["timestamp"], float(row["price"])
        end_ts = df.iloc[i + 1]["timestamp"] if i + 1 < len(df) else ts + timedelta(days=32)
        current = ts
        while current < end_ts:
            session.add(OilPrice(timestamp=current,
                                 open=price, high=price, low=price, close=price, volume=0.0))
            count += 1
            current += timedelta(hours=1)
            if count % 10000 == 0:
                session.commit()
                logger.info(f"  Seeded {count} oil rows...")

    session.commit()
    logger.info(f"Oil seed complete: {count} rows")
    return count


# ---------------------------------------------------------------------------
# Twelve Data — XAU/USD hourly
# ---------------------------------------------------------------------------

async def _fetch_twelve_data_gold() -> Optional[dict]:
    """
    ดึง XAU/USD hourly จาก Twelve Data
    Free tier: 800 credits/day, 8 req/min — 1 call ดึง 24 bars = 1 credit
    """
    key = settings.twelve_data_api_key
    if not key or key in ("demo", ""):
        logger.info("Twelve Data key not set — using demo fallback")
        return None

    params = {
        "symbol":     "XAU/USD",
        "interval":   "1h",
        "outputsize": "2",
        "apikey":     key,
        "format":     "JSON",
        "timezone":   "UTC",
        "end_date":   now_utc.strftime("%Y-%m-%d %H:%M:%S")
    }
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(f"{TWELVE_DATA_BASE}/time_series", params=params)
            resp.raise_for_status()
        data = resp.json()
        if data.get("status") == "error":
            logger.warning(f"Twelve Data error: {data.get('message')}")
            return None
        return data
    except Exception as e:
        logger.error(f"Twelve Data fetch failed: {e}")
        return None


def _parse_twelve_data_df(raw: dict) -> pd.DataFrame:
    rows = []
    for v in raw.get("values", []):
        try:
            rows.append({
                "timestamp": pd.to_datetime(v["datetime"]),
                "open":      float(v.get("open",   0)),
                "high":      float(v.get("high",   0)),
                "low":       float(v.get("low",    0)),
                "close":     float(v.get("close",  0)),
                "volume":    float(v.get("volume", 0)),
            })
        except Exception:
            continue
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values("timestamp").reset_index(drop=True)


async def fetch_and_save_gold(session: Session) -> int:
    logger.info("Fetching gold price (XAU/USD) from Twelve Data ...")
    raw = await _fetch_twelve_data_gold()

    if raw is None:
        logger.warning("No live gold data — using demo fallback")
        return await _save_demo_gold(session)

    df = _parse_twelve_data_df(raw)
    if df.empty:
        return 0

    count = 0
    for _, row in df.iterrows():
        crud.upsert_gold_price(session, GoldPrice(
            timestamp = row["timestamp"].to_pydatetime(),
            open=row["open"], high=row["high"],
            low=row["low"],   close=row["close"], volume=row["volume"],
        ))
        count += 1

    _compute_and_update_indicators(session)
    logger.info(f"Gold: saved {count} rows from Twelve Data")
    return count


# ---------------------------------------------------------------------------
# Twelve Data — WTI Crude Oil daily
# ---------------------------------------------------------------------------

async def _fetch_twelve_data_oil() -> Optional[pd.DataFrame]:
    """
    ดึง WTI daily price จาก Twelve Data (symbol=WTI, interval=1day)
    ใช้ API key เดียวกับ gold — real-time ไม่ lag เหมือน FRED
    """
    key = settings.twelve_data_api_key
    if not key or key == "demo":
        logger.warning("No Twelve Data API key — cannot fetch oil")
        return None

    params = {
        "symbol":     "WTI/USD",
        "interval":   "1day",
        "outputsize": 60,
        "apikey":     key,
        "timezone":   "UTC",
        "format":     "JSON",
    }
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(f"{TWELVE_DATA_BASE}/time_series", params=params)
            resp.raise_for_status()
            raw = resp.json()

        if raw.get("status") == "error" or "values" not in raw:
            logger.error(f"Twelve Data oil error: {raw.get('message', raw)}")
            return None

        rows = []
        for v in raw["values"]:
            try:
                rows.append({
                    "date":  pd.to_datetime(v["datetime"]),
                    "price": float(v["close"]),
                })
            except Exception:
                continue

        if not rows:
            return None

        df = pd.DataFrame(rows).sort_values("date").reset_index(drop=True)
        logger.info(f"Twelve Data oil: fetched {len(df)} daily bars, latest={df.iloc[-1]['price']:.2f}")
        return df

    except Exception as e:
        logger.error(f"Twelve Data oil fetch failed: {e}")
        return None


async def fetch_and_save_oil(session: Session) -> int:
    """
    ดึงราคา WTI daily จาก Twelve Data
    forward-fill เป็น hourly (เหมือน notebook Cell 8-10)
    """
    logger.info("Fetching oil price (WTI) from Twelve Data ...")
    df = await _fetch_twelve_data_oil()

    if df is None or df.empty:
        logger.warning("No Twelve Data oil — using demo fallback")
        return await _save_demo_oil(session)

    count = 0
    for _, row in df.iterrows():
        ts    = row["date"].to_pydatetime().replace(tzinfo=None)
        price = float(row["price"])
        for h in range(24):
            crud.upsert_oil_price(session, OilPrice(
                timestamp = ts.replace(hour=h, minute=0, second=0, microsecond=0),
                open=price, high=price, low=price, close=price, volume=0.0,
            ))
        count += 1

    logger.info(f"Oil: saved {count} daily records from Twelve Data (forward-filled hourly)")
    return count


# ---------------------------------------------------------------------------
# Technical Indicators
# ---------------------------------------------------------------------------

def _compute_and_update_indicators(session: Session):
    prices = crud.get_latest_gold_prices(session, limit=500)
    if len(prices) < 10:
        return
    prices_sorted = sorted(prices, key=lambda p: p.timestamp)
    closes = np.array([p.close for p in prices_sorted], dtype=np.float64)
    ema50  = _ema(closes, 50)
    ema200 = _ema(closes, 200)
    rsi14  = _rsi(closes, 14)
    macd_l, macd_s, macd_h = _macd(closes, 12, 26, 9)
    bb_u, bb_m, bb_l = _bollinger(closes, 20, 2.0)
    for i, price in enumerate(prices_sorted):
        price.ema_50      = float(ema50[i])  if not np.isnan(ema50[i])  else None
        price.ema_200     = float(ema200[i]) if not np.isnan(ema200[i]) else None
        price.rsi         = float(rsi14[i])  if not np.isnan(rsi14[i])  else None
        price.macd        = float(macd_l[i]) if not np.isnan(macd_l[i]) else None
        price.macd_signal = float(macd_s[i]) if not np.isnan(macd_s[i]) else None
        price.macd_hist   = float(macd_h[i]) if not np.isnan(macd_h[i]) else None
        price.bb_upper    = float(bb_u[i])   if not np.isnan(bb_u[i])   else None
        price.bb_mid      = float(bb_m[i])   if not np.isnan(bb_m[i])   else None
        price.bb_lower    = float(bb_l[i])   if not np.isnan(bb_l[i])   else None
        session.add(price)
    session.commit()


def _bollinger(arr: np.ndarray, period: int = 20, mult: float = 2.0):
    """Bollinger Bands — population stdev (same as TradingView default)."""
    n = len(arr)
    mid   = np.full(n, np.nan)
    upper = np.full(n, np.nan)
    lower = np.full(n, np.nan)
    for i in range(period - 1, n):
        w   = arr[i - period + 1 : i + 1]
        m   = w.mean()
        std = w.std(ddof=0)          # population stdev
        mid[i]   = m
        upper[i] = m + mult * std
        lower[i] = m - mult * std
    return upper, mid, lower


def _ema(arr: np.ndarray, period: int) -> np.ndarray:
    result = np.full(len(arr), np.nan)
    if len(arr) < period:
        return result
    k = 2.0 / (period + 1)
    result[period - 1] = arr[:period].mean()
    for i in range(period, len(arr)):
        result[i] = arr[i] * k + result[i - 1] * (1 - k)
    return result


def _rsi(arr: np.ndarray, period: int = 14) -> np.ndarray:
    result = np.full(len(arr), np.nan)
    if len(arr) < period + 1:
        return result
    delta  = np.diff(arr)
    gains  = np.where(delta > 0, delta, 0.0)
    losses = np.where(delta < 0, -delta, 0.0)
    avg_gain = gains[:period].mean()
    avg_loss = losses[:period].mean()
    for i in range(period, len(delta)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        rs = avg_gain / avg_loss if avg_loss != 0 else 100.0
        result[i + 1] = 100.0 - (100.0 / (1 + rs))
    return result


def _macd(arr: np.ndarray, fast=12, slow=26, signal=9):
    ema_fast = _ema(arr, fast)
    ema_slow = _ema(arr, slow)
    line     = np.where(np.isnan(ema_fast) | np.isnan(ema_slow), np.nan, ema_fast - ema_slow)
    # Fix: start signal EMA from first valid MACD value (avoid replacing NaN with 0)
    sig_line = np.full(len(line), np.nan)
    valid    = ~np.isnan(line)
    if valid.any():
        first = int(np.argmax(valid))
        sig_line[first:] = _ema(line[first:], signal)
    hist = np.where(np.isnan(line) | np.isnan(sig_line), np.nan, line - sig_line)
    return line, sig_line, hist


# ---------------------------------------------------------------------------
# Demo fallback
# ---------------------------------------------------------------------------

async def _save_demo_gold(session: Session) -> int:
    import random
    now, base, count = datetime.utcnow().replace(minute=0, second=0, microsecond=0), 3300.0, 0
    for i in range(24, 0, -1):
        ts    = now - timedelta(hours=i)
        close = base + random.gauss(0, 15); base = close
        crud.upsert_gold_price(session, GoldPrice(
            timestamp=ts, open=close + random.gauss(0, 3),
            high=close + abs(random.gauss(0, 5)),
            low=close - abs(random.gauss(0, 5)),
            close=close, volume=float(random.randint(100, 1000)),
        ))
        count += 1
    _compute_and_update_indicators(session)
    return count


async def _save_demo_oil(session: Session) -> int:
    import random
    now, base, count = datetime.utcnow().replace(minute=0, second=0, microsecond=0), 72.0, 0
    for i in range(24, 0, -1):
        ts = now - timedelta(hours=i)
        val = base + random.gauss(0, 0.5); base = val
        crud.upsert_oil_price(session, OilPrice(
            timestamp=ts, open=val, high=val+0.3, low=val-0.3, close=val, volume=0.0,
        ))
        count += 1
    return count
