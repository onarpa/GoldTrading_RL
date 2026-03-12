"""
Frontend Controller
===================
Endpoints ที่ Frontend ใช้ — aggregate data จากหลาย service
"""
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlmodel import Session
import os
from datetime import datetime

from database.database import get_session
from database import crud
from app.services.training_service import retrain_model
from app.core.config import get_settings
settings = get_settings()
from app.core.config import get_settings
settings = get_settings()

router = APIRouter(prefix="/api", tags=["frontend"])


@router.get("/dashboard")
def get_dashboard(session: Session = Depends(get_session)):
    """ข้อมูลรวมสำหรับ Dashboard"""
    # ราคาล่าสุด
    latest = crud.get_latest_gold(session)
    prices = crud.get_latest_gold_prices(session, limit=30)
    prices_sorted = sorted(prices, key=lambda p: p.timestamp)

    # prediction ล่าสุด
    pred = crud.get_latest_prediction(session)

    # oil ล่าสุด
    oil = crud.get_latest_oil(session)

    # คำนวณ price change
    price_change    = 0.0
    percent_change  = 0.0
    if len(prices_sorted) >= 2:
        current  = prices_sorted[-1].close
        previous = prices_sorted[-2].close
        price_change   = round(current - previous, 2)
        percent_change = round((price_change / previous) * 100, 2) if previous else 0.0

    return {
        "status": "success",
        "last_updated": datetime.utcnow().isoformat(),
        "current_price": latest.close if latest else 0,
        "price_change":  price_change,
        "percent_change": percent_change,
        "oil_price": oil.close if oil else 0,
        "technical": {
            "rsi":         latest.rsi if latest else None,
            "macd":        latest.macd if latest else None,
            "macd_signal": latest.macd_signal if latest else None,
            "ema_50":      latest.ema_50 if latest else None,
            "ema_200":     latest.ema_200 if latest else None,
        },
        "prediction": {
            "action":     pred.action if pred else "N/A",
            "confidence": round(pred.confidence, 3) if pred else 0,
            "tp_pct":     round(pred.tp_pct * 100, 2) if pred else 0,
            "sl_pct":     round(pred.sl_pct * 100, 2) if pred else 0,
            "tp_price":   round(pred.gold_price * (1 + pred.tp_pct) if pred and pred.action == "BUY" else pred.gold_price * (1 - pred.tp_pct), 2) if pred else 0,
            "sl_price":   round(pred.gold_price * (1 - pred.sl_pct) if pred and pred.action == "BUY" else pred.gold_price * (1 + pred.sl_pct), 2) if pred else 0,
            "timestamp":  pred.timestamp.isoformat() if pred else None,
        } if pred else None,
        "chart": {
            "labels": [p.timestamp.strftime("%m/%d %H:%M") for p in prices_sorted],
            "open":   [round(p.open,  2) for p in prices_sorted],
            "high":   [round(p.high,  2) for p in prices_sorted],
            "low":    [round(p.low,   2) for p in prices_sorted],
            "close":  [round(p.close, 2) for p in prices_sorted],
            "ema_50": [round(p.ema_50, 2) if p.ema_50 else None for p in prices_sorted],
            "ema_200":[round(p.ema_200, 2) if p.ema_200 else None for p in prices_sorted],
        }
    }


@router.get("/performance")
def get_performance(session: Session = Depends(get_session)):
    """ข้อมูล Model Performance"""
    metrics   = crud.get_latest_metrics(session)
    all_metrics = crud.get_all_metrics(session, limit=12)
    trades    = crud.get_trades(session, limit=200)
    logs      = crud.get_training_logs(session, limit=5)

    closed  = [t for t in trades if t.status != "OPEN"]
    wins    = [t for t in closed if t.status == "WIN"]
    losses  = [t for t in closed if t.status == "LOSS"]
    profit  = sum(t.profit or 0 for t in closed)
    win_rate = len(wins) / len(closed) * 100 if closed else 0
    pf = abs(sum(t.profit or 0 for t in wins) / sum(t.profit or 0 for t in losses)) if losses and sum(t.profit or 0 for t in losses) != 0 else 0

    # Monthly breakdown
    monthly = {}
    for t in closed:
        if t.close_time:
            key = t.close_time.strftime("%Y-%m")
            if key not in monthly:
                monthly[key] = {"trades": 0, "wins": 0, "profit": 0.0}
            monthly[key]["trades"] += 1
            if t.status == "WIN":
                monthly[key]["wins"] += 1
            monthly[key]["profit"] += t.profit or 0

    return {
        "status": "success",
        "summary": {
            "total_trades":   len(closed),
            "win_trades":     len(wins),
            "loss_trades":    len(losses),
            "win_rate":       round(win_rate, 1),
            "total_profit":   round(profit, 2),
            "profit_factor":  round(pf, 3),
            "sharpe_ratio":   round(metrics.sharpe_ratio, 3) if metrics else 0,
            "max_drawdown":   round(metrics.max_drawdown, 2) if metrics else 0,
            "avg_rr":         round(metrics.avg_rr, 3) if metrics else 0,
            "final_equity":   round(metrics.final_equity, 2) if metrics else 10000,
            "model_version":  metrics.model_version if metrics else "N/A",
            "eval_reward":    round(metrics.eval_reward, 2) if metrics else 0,
        },
        "monthly": [
            {
                "month":   k,
                "trades":  v["trades"],
                "wins":    v["wins"],
                "profit":  round(v["profit"], 2),
                "win_rate": round(v["wins"] / v["trades"] * 100, 1) if v["trades"] else 0,
            }
            for k, v in sorted(monthly.items())
        ],
        "training_logs": [{
            "id":           l.id,
            "started_at":   l.started_at.isoformat(),
            "finished_at":  l.finished_at.isoformat() if l.finished_at else None,
            "model_version": l.model_version,
            "status":       l.status,
            "timesteps":    l.timesteps,
            "best_reward":  round(l.best_reward, 2),
        } for l in logs],
    }


@router.get("/visualization")
def get_visualization(session: Session = Depends(get_session)):
    """ข้อมูล indicator สำหรับ DataVisualization — 500 bars ล่าสุด"""
    prices = crud.get_latest_gold_prices(session, limit=500)
    prices_sorted = sorted(prices, key=lambda p: p.timestamp)

    labels = [p.timestamp.strftime("%m/%d %H:%M") for p in prices_sorted]
    return {
        "status": "success",
        "labels": labels,
        "open":   [round(p.open,  2) for p in prices_sorted],
        "high":   [round(p.high,  2) for p in prices_sorted],
        "low":    [round(p.low,   2) for p in prices_sorted],
        "close":  [round(p.close, 2) for p in prices_sorted],
        "ema_50": [round(p.ema_50, 2) if p.ema_50 else None for p in prices_sorted],
        "ema_200":[round(p.ema_200, 2) if p.ema_200 else None for p in prices_sorted],
        "rsi":    [round(p.rsi, 2) if p.rsi else None for p in prices_sorted],
        "macd":   [round(p.macd, 4) if p.macd else None for p in prices_sorted],
        "macd_signal": [round(p.macd_signal, 4) if p.macd_signal else None for p in prices_sorted],
        "macd_hist":   [round(p.macd_hist, 4) if p.macd_hist else None for p in prices_sorted],
        "bb_upper":    [round(p.bb_upper, 2) if p.bb_upper else None for p in prices_sorted],
        "bb_mid":      [round(p.bb_mid,   2) if p.bb_mid   else None for p in prices_sorted],
        "bb_lower":    [round(p.bb_lower, 2) if p.bb_lower else None for p in prices_sorted],
    }


@router.post("/model/train")
async def trigger_training(session: Session = Depends(get_session)):
    """Trigger retrain โมเดลทันที"""
    result = await retrain_model(session, force=True)
    return result


@router.get("/model/training-logs")
def get_training_logs(session: Session = Depends(get_session)):
    """ดู training logs"""
    logs = crud.get_training_logs(session, limit=10)
    return {
        "status": "success",
        "logs": [{
            "id":           l.id,
            "started_at":   l.started_at.isoformat(),
            "finished_at":  l.finished_at.isoformat() if l.finished_at else None,
            "model_version": l.model_version,
            "status":       l.status,
            "timesteps":    l.timesteps,
            "best_reward":  round(l.best_reward, 2),
            "error":        l.error_message,
        } for l in logs]
    }


@router.get("/predictions/history")
def get_predictions_history(
    limit: int = Query(default=100, ge=1, le=500),
    session: Session = Depends(get_session),
):
    """ดู prediction history สำหรับ plot บน chart"""
    preds = crud.get_predictions(session, limit=limit)
    preds_sorted = sorted(preds, key=lambda p: p.timestamp)
    return {
        "status": "success",
        "count": len(preds_sorted),
        "predictions": [{
            "timestamp":       p.timestamp.strftime("%m/%d %H:%M"),
            "timestamp_iso":   p.timestamp.isoformat(),
            "price_timestamp": p.price_timestamp.strftime("%m/%d %H:%M"),
            "gold_price":      round(p.gold_price, 2),
            "action":          p.action,
            "direction_raw":   round(p.direction_raw, 4),
            "tp_pct":          round(p.tp_pct, 4),
            "sl_pct":          round(p.sl_pct, 4),
            "confidence":      round(p.confidence, 4),
            "tp_price":        round(p.gold_price * (1 + p.tp_pct) if p.action == "BUY" else p.gold_price * (1 - p.tp_pct), 2),
            "sl_price":        round(p.gold_price * (1 - p.sl_pct) if p.action == "BUY" else p.gold_price * (1 + p.sl_pct), 2),
        } for p in preds_sorted]
    }


@router.get("/model/list")
def list_models():
    """List .zip model files ใน RL_model/"""
    import glob
    model_dir = "./RL_model"
    files = sorted(glob.glob(f"{model_dir}/*.zip"))
    current = settings.model_path
    result = []
    for f in files:
        name = os.path.basename(f)
        size_mb = round(os.path.getsize(f) / 1024 / 1024, 1)
        result.append({
            "filename": name,
            "path": f,
            "size_mb": size_mb,
            "active": (f == current or f"./{f}" == current or name in current),
        })
    return {"status": "success", "models": result, "current": os.path.basename(current)}


class SelectModelBody(BaseModel):
    filename: str


@router.post("/model/select")
def select_model(body: SelectModelBody):
    """เปลี่ยน active model — clear cache ให้โหลดใหม่"""
    from app.services import model_service
    path = f"./RL_model/{body.filename}"
    if not os.path.exists(path):
        return {"status": "error", "error": f"File not found: {body.filename}"}
    version = body.filename.replace(".zip", "")
    settings.model_path    = path
    settings.model_version = version
    model_service._model   = None
    return {"status": "success", "message": f"Active model → {body.filename}", "version": version}


@router.get("/scheduler/status")
def scheduler_status():
    """ดู scheduler jobs ทั้งหมด — ใช้ debug ว่า predict/fetch ทำงานมั้ย"""
    from app.services.scheduler_service import scheduler
    jobs = []
    for job in scheduler.get_jobs():
        next_run = job.next_run_time
        jobs.append({
            "id":       job.id,
            "next_run": next_run.isoformat() if next_run else None,
            "next_run_thai": (
                next_run.astimezone().isoformat() if next_run else "—"
            ),
        })
    return {
        "status":  "success",
        "running": scheduler.running,
        "jobs":    jobs,
    }


@router.get("/model/debug")
def model_debug():
    """Debug model loading — แสดง path, file exists, error detail"""
    import traceback
    path = settings.model_path
    result = {
        "model_path":   path,
        "file_exists":  os.path.exists(path),
        "file_size_kb": round(os.path.getsize(path) / 1024, 1) if os.path.exists(path) else 0,
        "loaded":       False,
        "obs_dim":      None,
        "error":        None,
    }
    if result["file_exists"]:
        try:
            from stable_baselines3 import PPO
            m = PPO.load(path)
            result["loaded"]  = True
            result["obs_dim"] = m.observation_space.shape[0]
        except Exception as e:
            result["error"] = traceback.format_exc()
    return result


@router.get("/scheduler/status")
def scheduler_status():
    """ดู scheduler jobs — debug ว่า fetch/predict ทำงานมั้ย"""
    from app.services.scheduler_service import scheduler
    jobs = []
    for job in scheduler.get_jobs():
        nxt = job.next_run_time
        jobs.append({
            "id":       job.id,
            "next_run": nxt.isoformat() if nxt else None,
        })
    return {"status": "success", "running": scheduler.running, "jobs": jobs}


@router.get("/trades/chart")
def get_trades_chart(
    limit: int = Query(default=100, ge=1, le=500),
    session: Session = Depends(get_session),
):
    """Trades สำหรับ chart overlay — เฉพาะ trade ที่โมเดลเปิดจริง"""
    trades = crud.get_trades(session, limit=limit)
    result = []
    for t in sorted(trades, key=lambda x: x.open_time):
        result.append({
            "price_timestamp": t.open_time.isoformat(),
            "action":          t.direction,
            "entry_price":     round(t.entry_price, 2),
            "tp_price":        round(t.tp_price, 2),
            "sl_price":        round(t.sl_price, 2),
            "confidence":      1.0,
            "status":          t.status,
        })
    return {"status": "success", "data": result}
