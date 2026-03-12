"""
Price Controller
================
Endpoints สำหรับราคาทองคำและน้ำมัน
"""
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session
from datetime import datetime, timedelta

from database.database import get_session
from database import crud
from app.services.price_service import fetch_and_save_gold, fetch_and_save_oil

router = APIRouter(prefix="/api/prices", tags=["prices"])


@router.post("/fetch")
async def manual_fetch(session: Session = Depends(get_session)):
    """Trigger ดึงราคาทองคำและน้ำมันทันที"""
    gold_count = await fetch_and_save_gold(session)
    oil_count  = await fetch_and_save_oil(session)
    return {
        "status": "success",
        "gold_rows": gold_count,
        "oil_rows": oil_count,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/gold/latest")
def get_latest_gold(session: Session = Depends(get_session)):
    """ราคาทองคำล่าสุด"""
    price = crud.get_latest_gold(session)
    if not price:
        return {"status": "no_data"}
    return {
        "status": "success",
        "timestamp": price.timestamp.isoformat(),
        "open":  price.open,
        "high":  price.high,
        "low":   price.low,
        "close": price.close,
        "volume": price.volume,
        "indicators": {
            "ema_50":      price.ema_50,
            "ema_200":     price.ema_200,
            "rsi":         price.rsi,
            "macd":        price.macd,
            "macd_signal": price.macd_signal,
            "macd_hist":   price.macd_hist,
        }
    }


@router.get("/gold/history")
def get_gold_history(
    hours: int = Query(default=0, ge=0, le=8760),
    limit: int = Query(default=500, ge=1, le=2000),
    session: Session = Depends(get_session),
):
    """ราคาทองคำย้อนหลัง — ถ้า hours=0 ใช้ limit bars แทน"""
    if hours > 0:
        since  = datetime.utcnow() - timedelta(hours=hours)
        prices = crud.get_gold_prices_since(session, since)
        prices_sorted = sorted(prices, key=lambda p: p.timestamp)
    else:
        prices = crud.get_latest_gold_prices(session, limit=limit)
        prices_sorted = sorted(prices, key=lambda p: p.timestamp)
    return {
        "status": "success",
        "count": len(prices_sorted),
        "data": [{
            "timestamp": p.timestamp.isoformat(),
            "open":  p.open,
            "high":  p.high,
            "low":   p.low,
            "close": p.close,
            "volume": p.volume,
            "rsi":    p.rsi,
            "macd":   p.macd,
            "macd_signal": p.macd_signal,
            "ema_50":  p.ema_50,
            "ema_200": p.ema_200,
        } for p in prices_sorted]
    }


@router.get("/oil/latest")
def get_latest_oil(session: Session = Depends(get_session)):
    """ราคาน้ำมันล่าสุด"""
    price = crud.get_latest_oil(session)
    if not price:
        return {"status": "no_data"}
    return {
        "status": "success",
        "timestamp": price.timestamp.isoformat(),
        "close": price.close,
    }
