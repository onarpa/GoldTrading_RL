"""
Model Service
=============
โหลด PPO model (+Oil config) และ predict จากราคาล่าสุดใน DB

Model: best_model_ppo_1M_oil_medRisk_noSeed.zip
Notebook training config (FinalPcolab2.ipynb):
  use_oil_price=True, use_rsi=False, use_macd=False,
  use_support_resistance=False, use_trend_regime=True,
  risk_bounds=(0.005, 0.015), min_rr=1.1

Observation vector (obs_dim = 14):
  [0-4]   MinMaxScaler(OHLCV)            -- fit on train 2005-2023
  [5]     (close - EMA50) / close
  [6]     (close - EMA200) / close
  [7]     (EMA50 - EMA200) / close
  [8]     EMA50 slope (24-bar)
  [9]     EMA200 slope (24-bar)
  [10]    StandardScaler(oil_price)      -- fit on oil train 2005-2023
  [11]    balance / initial_balance      = 1.0
  [12]    equity  / initial_balance      = 1.0
  [13]    open_orders / max_orders       = 0.0

Scaler parameters (computed from XAU_1h_data.csv + crude-oil-price.csv, train set 2005-2023):

  MinMaxScaler (gold OHLCV):
    Open  : min=381.30,  scale=1736.23
    High  : min=382.00,  scale=1762.77
    Low   : min=381.10,  scale=1709.73
    Close : min=381.80,  scale=1735.73
    Volume: min=1.00,    scale=79714.00

  StandardScaler (oil):
    mean=71.872485, std=21.546321
"""
import numpy as np
import logging
from datetime import datetime
from sqlmodel import Session, select
from typing import Optional
import os

from app.core.config import get_settings
from database.models import Prediction, Trade, GoldPrice
from database import crud

logger   = logging.getLogger(__name__)
settings = get_settings()

_model = None

# ---------------------------------------------------------------------------
# Scaler parameters (computed from training data 2005-2023)
# ---------------------------------------------------------------------------

_OIL_MEAN = 71.872485
_OIL_STD  = 21.546321
_VOLUME_MEDIAN = 2546.0

_gold_scaler_cache: dict = {}
_gold_scaler_ts: float   = 0.0
_SCALER_TTL = 1800  # refit ทุก 30 นาที


def _get_gold_scaler(prices: list) -> dict:
    import time
    global _gold_scaler_cache, _gold_scaler_ts
    now = time.time()
    if _gold_scaler_cache and (now - _gold_scaler_ts) < _SCALER_TTL:
        return _gold_scaler_cache
    def _mm(arr):
        mn = float(arr.min()); mx = float(arr.max())
        return {"min": mn, "scale": (mx - mn) if mx != mn else 1.0}
    opens   = np.array([p.open   for p in prices], dtype=np.float64)
    highs   = np.array([p.high   for p in prices], dtype=np.float64)
    lows    = np.array([p.low    for p in prices], dtype=np.float64)
    closes  = np.array([p.close  for p in prices], dtype=np.float64)
    raw_vols = np.array([p.volume for p in prices], dtype=np.float64)
    volumes = raw_vols if raw_vols.max() > 0 else np.full(len(raw_vols), _VOLUME_MEDIAN)
    _gold_scaler_cache = {
        "Open": _mm(opens), "High": _mm(highs), "Low": _mm(lows),
        "Close": _mm(closes), "Volume": _mm(volumes),
    }
    _gold_scaler_ts = now
    logger.info(
        f"Gold scaler refit: Close min={_gold_scaler_cache['Close']['min']:.2f} "
        f"scale={_gold_scaler_cache['Close']['scale']:.2f} ({len(prices)} bars)"
    )
    return _gold_scaler_cache


def _scale_gold_ohlcv(o, h, l, c, v, scaler):
    return np.array([
        (o - scaler["Open"]["min"])   / scaler["Open"]["scale"],
        (h - scaler["High"]["min"])   / scaler["High"]["scale"],
        (l - scaler["Low"]["min"])    / scaler["Low"]["scale"],
        (c - scaler["Close"]["min"])  / scaler["Close"]["scale"],
        (v - scaler["Volume"]["min"]) / scaler["Volume"]["scale"],
    ], dtype=np.float32)


def _scale_oil(raw_price: float) -> float:
    return (raw_price - _OIL_MEAN) / _OIL_STD


# ---------------------------------------------------------------------------
# Model loader
# ---------------------------------------------------------------------------

def _load_model():
    global _model
    if _model is not None:
        return _model
    path = settings.model_path
    if not os.path.exists(path):
        logger.warning(f"Model file not found: {path} — using fallback HOLD")
        return None
    try:
        from stable_baselines3 import PPO
        _model = PPO.load(path)
        actual = _model.observation_space.shape[0]
        logger.info(f"Model loaded OK | obs_dim={actual} | path={path}")
        if actual != settings.model_obs_dim:
            logger.warning(f"obs_dim mismatch: model={actual}, config={settings.model_obs_dim}.")
    except Exception as e:
        logger.error(f"Failed to load model: {e}", exc_info=True)
        _model = None
    return _model


# ---------------------------------------------------------------------------
# Observation builder
# ---------------------------------------------------------------------------

def _ema_series(arr: np.ndarray, period: int) -> np.ndarray:
    result = np.full(len(arr), np.nan)
    if len(arr) < period:
        return result
    k = 2.0 / (period + 1)
    result[period - 1] = arr[:period].mean()
    for i in range(period, len(arr)):
        result[i] = arr[i] * k + result[i - 1] * (1 - k)
    return result


def _build_observation(prices: list, oil_price_raw: float) -> Optional[np.ndarray]:
    if len(prices) < 50:
        logger.warning(f"Not enough data for obs: {len(prices)} (need >= 50)")
        return None

    closes  = np.array([p.close for p in prices], dtype=np.float64)
    latest  = prices[-1]
    close_n = float(closes[-1])
    norm    = close_n if close_n > 0 else 1.0

    scaler = _get_gold_scaler(prices)
    ohlcv  = _scale_gold_ohlcv(
        o=float(latest.open), h=float(latest.high),
        l=float(latest.low),  c=close_n,
        v=float(latest.volume) if float(latest.volume) > 0 else _VOLUME_MEDIAN,
        scaler=scaler,
    )

    ema50_arr  = _ema_series(closes, 50)
    ema200_arr = _ema_series(closes, 200)
    ema50_now  = float(ema50_arr[-1])  if not np.isnan(ema50_arr[-1])  else close_n
    ema200_now = float(ema200_arr[-1]) if not np.isnan(ema200_arr[-1]) else close_n

    price_vs_fast = (close_n - ema50_now)  / norm
    price_vs_slow = (close_n - ema200_now) / norm
    ema_cross     = (ema50_now - ema200_now) / norm

    SLOPE_WIN = 24
    if len(closes) >= SLOPE_WIN + 1 and not np.isnan(ema50_arr[-(SLOPE_WIN + 1)]):
        d50  = abs(float(ema50_arr[-(SLOPE_WIN + 1)])) or 1.0
        d200 = abs(float(ema200_arr[-(SLOPE_WIN + 1)])) or 1.0
        ema50_slope  = (ema50_now  - float(ema50_arr[-(SLOPE_WIN + 1)]))  / d50
        ema200_slope = (ema200_now - float(ema200_arr[-(SLOPE_WIN + 1)])) / d200
    else:
        ema50_slope = ema200_slope = 0.0

    trend   = np.array([price_vs_fast, price_vs_slow, ema_cross, ema50_slope, ema200_slope], dtype=np.float32)
    oil_s   = np.array([_scale_oil(oil_price_raw)], dtype=np.float32)
    account = np.array([1.0, 1.0, 0.0], dtype=np.float32)

    obs = np.concatenate([ohlcv, trend, oil_s, account])
    expected = settings.model_obs_dim
    if obs.shape[0] != expected:
        logger.error(f"obs_dim built={obs.shape[0]} expected={expected}")
        obs = obs[:expected] if obs.shape[0] > expected else np.pad(obs, (0, expected - obs.shape[0]))

    return np.nan_to_num(obs.astype(np.float32), nan=0.0, posinf=0.0, neginf=0.0)


# ---------------------------------------------------------------------------
# Predict and save
# ---------------------------------------------------------------------------

def _fallback_action() -> dict:
    return {"action": "HOLD", "direction_raw": 0.0, "tp_pct": 0.010,
            "sl_pct": 0.005, "risk_pct": 0.010, "confidence": 0.0}


async def predict_only(session: Session) -> Optional[Prediction]:
    return await _predict_core(session, open_trade=False)


async def predict_and_save(session: Session) -> Optional[Prediction]:
    return await _predict_core(session, open_trade=True)


async def _predict_core(session: Session, open_trade: bool = True) -> Optional[Prediction]:
    prices = crud.get_latest_gold_prices(session, limit=300)
    if not prices:
        logger.warning("No gold price data for prediction")
        return None

    prices_sorted = sorted(prices, key=lambda p: p.timestamp)
    latest        = prices_sorted[-1]
    oil_row       = crud.get_latest_oil(session)
    oil_price_raw = oil_row.close if oil_row else 72.0

    obs   = _build_observation(prices_sorted, oil_price_raw)
    model = _load_model()

    if model is not None and obs is not None:
        try:
            raw_action, _ = model.predict(obs, deterministic=True)
            direction_raw = float(np.tanh(raw_action[0]))
            tp_raw   = float(raw_action[1])
            sl_raw   = float(raw_action[2])
            risk_raw = float(raw_action[3]) if len(raw_action) > 3 else 0.0

            TP_MIN, TP_MAX     = 0.006, 0.015
            SL_MIN, SL_MAX     = 0.003, 0.008
            RISK_MIN, RISK_MAX = 0.005, 0.015

            tp_pct   = float(np.clip(TP_MIN   + (tp_raw   + 1) / 2 * (TP_MAX   - TP_MIN),   TP_MIN,   TP_MAX))
            sl_pct   = float(np.clip(SL_MIN   + (sl_raw   + 1) / 2 * (SL_MAX   - SL_MIN),   SL_MIN,   SL_MAX))
            risk_pct = float(np.clip(RISK_MIN + (risk_raw + 1) / 2 * (RISK_MAX - RISK_MIN), RISK_MIN, RISK_MAX))
            action     = "BUY" if direction_raw > 0.1 else "SELL" if direction_raw < -0.1 else "HOLD"
            confidence = abs(direction_raw)
        except Exception as e:
            logger.error(f"Prediction error: {e}", exc_info=True)
            fb = _fallback_action()
            direction_raw, tp_pct, sl_pct, risk_pct = fb["direction_raw"], fb["tp_pct"], fb["sl_pct"], fb["risk_pct"]
            action, confidence = fb["action"], fb["confidence"]
    else:
        logger.info("No model — using fallback action")
        fb = _fallback_action()
        direction_raw, tp_pct, sl_pct, risk_pct = fb["direction_raw"], fb["tp_pct"], fb["sl_pct"], fb["risk_pct"]
        action, confidence = fb["action"], fb["confidence"]

    pred = Prediction(
        timestamp=datetime.utcnow(), price_timestamp=latest.timestamp,
        gold_price=latest.close, action=action, direction_raw=direction_raw,
        tp_pct=tp_pct, sl_pct=sl_pct, risk_pct=risk_pct, confidence=confidence,
        model_version=settings.model_version,
    )
    saved = crud.upsert_prediction_by_hour(session, pred)

    if open_trade and action in ("BUY", "SELL") and confidence > 0.1:
        open_trades = crud.get_open_trades(session)
        if open_trades:
            logger.info(f"Skipping new {action} — {len(open_trades)} OPEN order(s) exist")
        else:
            entry    = latest.close
            tp_price = entry * (1 + tp_pct) if action == "BUY" else entry * (1 - tp_pct)
            sl_price = entry * (1 - sl_pct) if action == "BUY" else entry * (1 + sl_pct)
            lots     = float(np.clip((10000.0 * risk_pct) / (entry * sl_pct * 100), 0.01, 5.0))
            trade = Trade(
                open_time=datetime.utcnow(), direction=action,
                entry_price=entry, tp_price=tp_price, sl_price=sl_price,
                lots=lots, status="OPEN", prediction_id=saved.id,
            )
            crud.save_trade(session, trade)

    # ── ตรวจ open trades ทุกครั้ง (ทั้งตอน predict และตอน fetch ราคา)
    if open_trade:
        closed = check_open_trades(session)
        if closed:
            logger.info(f"Auto-closed {closed} trade(s) after prediction")

    logger.info(
        f"Prediction: {action} | gold={latest.close:.2f} "
        f"oil_raw={oil_price_raw:.2f} oil_scaled={_scale_oil(oil_price_raw):.3f} | "
        f"conf={confidence:.3f} | tp={tp_pct*100:.3f}% sl={sl_pct*100:.3f}%"
    )
    return saved


# ---------------------------------------------------------------------------
# Trade closer — scan ALL bars since trade open_time (BUG FIX)
# ---------------------------------------------------------------------------

def check_open_trades(session: Session) -> int:
    """
    ตรวจสอบ open trades ทั้งหมด โดย scan ทุก bar ตั้งแต่เวลา open_time
    ของแต่ละ trade จนถึงปัจจุบัน และปิด trade ที่ bar แรกที่ hit TP/SL

    BUG เดิม: _check_open_trades() ตรวจแค่ bar เดียว (latest bar)
              → trade ไม่ปิดเมื่อ TP/SL ถูก hit ในช่วง bars ที่ผ่านมา

    FIX:      ดึงทุก bar ตั้งแต่ trade.open_time เรียงเก่า→ใหม่
              scan ทีละ bar → ปิดที่ bar แรกที่ hit (TP check ก่อน SL)

    คืนค่า:   จำนวน trade ที่ถูกปิดในรอบนี้
    """
    open_trades = crud.get_open_trades(session)
    if not open_trades:
        return 0

    closed_count = 0
    for trade in open_trades:
        # ดึง bars ทั้งหมดตั้งแต่ trade เปิด เรียงเก่า → ใหม่
        bars: list[GoldPrice] = session.exec(
            select(GoldPrice)
            .where(GoldPrice.timestamp >= trade.open_time)
            .order_by(GoldPrice.timestamp)
        ).all()

        if not bars:
            continue

        hit_status: Optional[str]     = None
        hit_price:  Optional[float]   = None
        hit_time:   Optional[datetime] = None

        for bar in bars:
            if trade.direction == "BUY":
                if bar.high >= trade.tp_price:          # TP hit
                    hit_status, hit_price, hit_time = "WIN",  trade.tp_price, bar.timestamp
                    break
                if bar.low <= trade.sl_price:           # SL hit
                    hit_status, hit_price, hit_time = "LOSS", trade.sl_price, bar.timestamp
                    break
            else:  # SELL
                if bar.low <= trade.tp_price:           # TP hit (short)
                    hit_status, hit_price, hit_time = "WIN",  trade.tp_price, bar.timestamp
                    break
                if bar.high >= trade.sl_price:          # SL hit (short)
                    hit_status, hit_price, hit_time = "LOSS", trade.sl_price, bar.timestamp
                    break

        if hit_status:
            crud.close_trade(session, trade.id, hit_price, hit_time, hit_status)
            closed_count += 1
            logger.info(
                f"Trade #{trade.id} closed [{hit_status}] | "
                f"dir={trade.direction} entry={trade.entry_price:.2f} "
                f"exit={hit_price:.2f} @ {hit_time}"
            )
        else:
            logger.debug(
                f"Trade #{trade.id} still OPEN | "
                f"tp={trade.tp_price:.2f} sl={trade.sl_price:.2f} "
                f"bars_checked={len(bars)}"
            )

    return closed_count


def reload_model():
    global _model
    _model = None
    return _load_model()
