"""
Prediction Controller
=====================
Endpoints สำหรับ prediction และ trade
"""
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session
from datetime import datetime

from database.database import get_session
from database import crud
from app.services.model_service import predict_and_save, predict_only

router = APIRouter(prefix="/api/predictions", tags=["predictions"])


@router.post("/predict")
async def manual_predict(session: Session = Depends(get_session)):
    """แนะนำผู้ใช้ ณ เวลานั้น — ไม่เปิด Trade"""
    pred = await predict_only(session)
    if not pred:
        return {"status": "error", "message": "No price data available"}
    return {
        "status": "success",
        "prediction": {
            "timestamp":    pred.timestamp.isoformat(),
            "gold_price":   pred.gold_price,
            "action":       pred.action,
            "confidence":   round(pred.confidence, 3),
            "tp_pct":       round(pred.tp_pct * 100, 3),
            "sl_pct":       round(pred.sl_pct * 100, 3),
            "tp_price":     round(pred.gold_price * (1 + pred.tp_pct) if pred.action == "BUY" else pred.gold_price * (1 - pred.tp_pct), 2),
            "sl_price":     round(pred.gold_price * (1 - pred.sl_pct) if pred.action == "BUY" else pred.gold_price * (1 + pred.sl_pct), 2),
            "risk_pct":     round(pred.risk_pct * 100, 3),
            "model_version": pred.model_version,
        }
    }


@router.get("/latest")
def get_latest_prediction(session: Session = Depends(get_session)):
    """ผล prediction ล่าสุด"""
    pred = crud.get_latest_prediction(session)
    if not pred:
        return {"status": "no_data"}
    return {
        "status": "success",
        "prediction": {
            "timestamp":    pred.timestamp.isoformat(),
            "gold_price":   pred.gold_price,
            "action":       pred.action,
            "confidence":   round(pred.confidence, 3),
            "tp_pct":       round(pred.tp_pct * 100, 3),
            "sl_pct":       round(pred.sl_pct * 100, 3),
            "tp_price":     round(pred.gold_price * (1 + pred.tp_pct) if pred.action == "BUY" else pred.gold_price * (1 - pred.tp_pct), 2),
            "sl_price":     round(pred.gold_price * (1 - pred.sl_pct) if pred.action == "BUY" else pred.gold_price * (1 + pred.sl_pct), 2),
            "risk_pct":     round(pred.risk_pct * 100, 3),
            "model_version": pred.model_version,
        }
    }


@router.get("/history")
def get_prediction_history(
    limit: int = Query(default=100, ge=1, le=500),
    session: Session = Depends(get_session),
):
    """ประวัติ prediction พร้อม entry/tp/sl price สำหรับ chart overlay"""
    preds = crud.get_predictions(session, limit=limit)
    result = []
    for p in preds:
        entry    = p.gold_price
        tp_price = entry * (1 + p.tp_pct) if p.action == "BUY" else entry * (1 - p.tp_pct)
        sl_price = entry * (1 - p.sl_pct) if p.action == "BUY" else entry * (1 + p.sl_pct)
        result.append({
            "timestamp":       p.timestamp.isoformat(),
            "price_timestamp": p.price_timestamp.isoformat(),
            "gold_price":      p.gold_price,
            "action":          p.action,
            "confidence":      round(p.confidence, 3),
            "tp_pct":          round(p.tp_pct * 100, 3),
            "sl_pct":          round(p.sl_pct * 100, 3),
            "entry_price":     round(entry, 2),
            "tp_price":        round(tp_price, 2),
            "sl_price":        round(sl_price, 2),
            "model_version":   p.model_version,
        })
    return {"status": "success", "count": len(result), "data": result}


@router.get("/trades")
def get_trades(
    limit: int = Query(default=100, ge=1, le=500),
    session: Session = Depends(get_session),
):
    """ประวัติ trade"""
    trades = crud.get_trades(session, limit=limit)
    closed = [t for t in trades if t.status != "OPEN"]
    open_t = [t for t in trades if t.status == "OPEN"]
    wins   = [t for t in closed if t.status == "WIN"]
    losses = [t for t in closed if t.status == "LOSS"]

    total_profit = sum(t.profit or 0 for t in closed)
    win_rate = len(wins) / len(closed) * 100 if closed else 0

    return {
        "status": "success",
        "summary": {
            "total_trades":  len(closed),
            "open_trades":   len(open_t),
            "win_trades":    len(wins),
            "loss_trades":   len(losses),
            "win_rate":      round(win_rate, 1),
            "total_profit":  round(total_profit, 2),
        },
        "trades": [{
            "id":          t.id,
            "open_time":   t.open_time.isoformat(),
            "close_time":  t.close_time.isoformat() if t.close_time else None,
            "direction":   t.direction,
            "entry_price": t.entry_price,
            "exit_price":  t.exit_price,
            "tp_price":    t.tp_price,
            "sl_price":    t.sl_price,
            "lots":        round(t.lots, 4),
            "profit":      round(t.profit, 2) if t.profit else None,
            "status":      t.status,
        } for t in trades]
    }
