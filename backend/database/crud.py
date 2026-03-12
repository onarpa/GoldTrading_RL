from sqlmodel import Session, select, desc
from database.models import GoldPrice, OilPrice, Prediction, Trade, ModelMetrics, TrainingLog
from datetime import datetime, timedelta
from typing import Optional


# ─── Gold Price ───────────────────────────────────────────────────────────────

def upsert_gold_price(session: Session, data: GoldPrice) -> GoldPrice:
    existing = session.exec(
        select(GoldPrice).where(GoldPrice.timestamp == data.timestamp)
    ).first()
    if existing:
        for key, val in data.model_dump(exclude={"id", "created_at"}).items():
            if val is not None:
                setattr(existing, key, val)
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return existing
    session.add(data)
    session.commit()
    session.refresh(data)
    return data


def get_latest_gold_prices(session: Session, limit: int = 200) -> list[GoldPrice]:
    return session.exec(
        select(GoldPrice).order_by(desc(GoldPrice.timestamp)).limit(limit)
    ).all()


def get_gold_prices_since(session: Session, since: datetime) -> list[GoldPrice]:
    return session.exec(
        select(GoldPrice)
        .where(GoldPrice.timestamp >= since)
        .order_by(GoldPrice.timestamp)
    ).all()


def get_latest_gold(session: Session) -> Optional[GoldPrice]:
    return session.exec(
        select(GoldPrice).order_by(desc(GoldPrice.timestamp)).limit(1)
    ).first()


# ─── Oil Price ────────────────────────────────────────────────────────────────

def upsert_oil_price(session: Session, data: OilPrice) -> OilPrice:
    existing = session.exec(
        select(OilPrice).where(OilPrice.timestamp == data.timestamp)
    ).first()
    if existing:
        for key, val in data.model_dump(exclude={"id", "created_at"}).items():
            if val is not None:
                setattr(existing, key, val)
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return existing
    session.add(data)
    session.commit()
    session.refresh(data)
    return data


def get_latest_oil(session: Session) -> Optional[OilPrice]:
    return session.exec(
        select(OilPrice).order_by(desc(OilPrice.timestamp)).limit(1)
    ).first()


def get_oil_prices_since(session: Session, since: datetime) -> list[OilPrice]:
    return session.exec(
        select(OilPrice)
        .where(OilPrice.timestamp >= since)
        .order_by(OilPrice.timestamp)
    ).all()


# ─── Prediction ───────────────────────────────────────────────────────────────

def save_prediction(session: Session, pred: Prediction) -> Prediction:
    session.add(pred)
    session.commit()
    session.refresh(pred)
    return pred


def upsert_prediction_by_hour(session: Session, pred: Prediction) -> Prediction:
    """ถ้ามี prediction ในชั่วโมงเดียวกันแล้ว ให้ update แทน insert ใหม่"""
    from datetime import timezone
    ts = pred.timestamp.replace(minute=0, second=0, microsecond=0)
    ts_next = ts.replace(hour=(ts.hour + 1) % 24) if ts.hour < 23 else ts.replace(hour=0)
    existing = session.exec(
        select(Prediction)
        .where(Prediction.timestamp >= ts)
        .where(Prediction.timestamp < ts_next if ts.hour < 23
               else Prediction.timestamp >= ts)
        .order_by(desc(Prediction.timestamp))
        .limit(1)
    ).first()
    if existing:
        existing.timestamp       = pred.timestamp
        existing.price_timestamp = pred.price_timestamp
        existing.gold_price      = pred.gold_price
        existing.action          = pred.action
        existing.direction_raw   = pred.direction_raw
        existing.tp_pct          = pred.tp_pct
        existing.sl_pct          = pred.sl_pct
        existing.risk_pct        = pred.risk_pct
        existing.confidence      = pred.confidence
        existing.model_version   = pred.model_version
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return existing
    session.add(pred)
    session.commit()
    session.refresh(pred)
    return pred


def get_latest_prediction(session: Session) -> Optional[Prediction]:
    return session.exec(
        select(Prediction).order_by(desc(Prediction.timestamp)).limit(1)
    ).first()


def get_predictions(session: Session, limit: int = 100) -> list[Prediction]:
    return session.exec(
        select(Prediction).order_by(desc(Prediction.timestamp)).limit(limit)
    ).all()


# ─── Trade ───────────────────────────────────────────────────────────────────

def save_trade(session: Session, trade: Trade) -> Trade:
    session.add(trade)
    session.commit()
    session.refresh(trade)
    return trade


def get_open_trades(session: Session) -> list[Trade]:
    return session.exec(
        select(Trade).where(Trade.status == "OPEN")
    ).all()


def get_trades(session: Session, limit: int = 200) -> list[Trade]:
    return session.exec(
        select(Trade).order_by(desc(Trade.open_time)).limit(limit)
    ).all()


def close_trade(session: Session, trade_id: int, exit_price: float,
                close_time: datetime, status: str) -> Optional[Trade]:
    trade = session.get(Trade, trade_id)
    if not trade:
        return None
    trade.exit_price = exit_price
    trade.close_time = close_time
    trade.status = status
    if trade.direction == "BUY":
        trade.profit = (exit_price - trade.entry_price) * trade.lots * 100
    else:
        trade.profit = (trade.entry_price - exit_price) * trade.lots * 100
    session.add(trade)
    session.commit()
    session.refresh(trade)
    return trade


# ─── Model Metrics ────────────────────────────────────────────────────────────

def save_metrics(session: Session, metrics: ModelMetrics) -> ModelMetrics:
    session.add(metrics)
    session.commit()
    session.refresh(metrics)
    return metrics


def get_latest_metrics(session: Session) -> Optional[ModelMetrics]:
    return session.exec(
        select(ModelMetrics).order_by(desc(ModelMetrics.recorded_at)).limit(1)
    ).first()


def get_all_metrics(session: Session, limit: int = 12) -> list[ModelMetrics]:
    return session.exec(
        select(ModelMetrics).order_by(desc(ModelMetrics.recorded_at)).limit(limit)
    ).all()


# ─── Training Log ─────────────────────────────────────────────────────────────

def create_training_log(session: Session, log: TrainingLog) -> TrainingLog:
    session.add(log)
    session.commit()
    session.refresh(log)
    return log


def update_training_log(session: Session, log_id: int, **kwargs) -> Optional[TrainingLog]:
    log = session.get(TrainingLog, log_id)
    if not log:
        return None
    for k, v in kwargs.items():
        setattr(log, k, v)
    session.add(log)
    session.commit()
    session.refresh(log)
    return log


def get_training_logs(session: Session, limit: int = 10) -> list[TrainingLog]:
    return session.exec(
        select(TrainingLog).order_by(desc(TrainingLog.started_at)).limit(limit)
    ).all()
