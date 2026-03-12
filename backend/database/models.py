from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class GoldPrice(SQLModel, table=True):
    """ราคาทองคำรายชั่วโมง จาก AlphaVantage"""
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(index=True, unique=True)
    open: float
    high: float
    low: float
    close: float
    volume: float = Field(default=0.0)
    # Technical indicators (คำนวณเมื่อ insert)
    ema_50: Optional[float] = None
    ema_200: Optional[float] = None
    rsi: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_hist: Optional[float] = None
    sr_support: Optional[float] = None
    sr_resistance: Optional[float] = None
    bb_upper: Optional[float] = None
    bb_mid: Optional[float] = None
    bb_lower: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class OilPrice(SQLModel, table=True):
    """ราคาน้ำมันรายชั่วโมง จาก AlphaVantage"""
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(index=True, unique=True)
    open: float
    high: float
    low: float
    close: float
    volume: float = Field(default=0.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Prediction(SQLModel, table=True):
    """ผลการ predict ของโมเดล"""
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(index=True)           # เวลาที่ predict
    price_timestamp: datetime                          # เวลาของ price ที่ใช้
    gold_price: float                                  # ราคา gold ณ เวลานั้น
    action: str                                        # BUY / SELL / HOLD
    direction_raw: float                               # raw action[0] จากโมเดล
    tp_pct: float                                      # take profit %
    sl_pct: float                                      # stop loss %
    risk_pct: float                                    # risk %
    confidence: float                                  # |direction_raw| normalised
    model_version: str = Field(default="v1")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Trade(SQLModel, table=True):
    """Trade ที่เปิด/ปิดแล้ว (simulate จาก prediction)"""
    id: Optional[int] = Field(default=None, primary_key=True)
    open_time: datetime
    close_time: Optional[datetime] = None
    direction: str                                     # BUY / SELL
    entry_price: float
    exit_price: Optional[float] = None
    tp_price: float
    sl_price: float
    lots: float
    profit: Optional[float] = None
    status: str = Field(default="OPEN")               # OPEN / WIN / LOSS
    prediction_id: Optional[int] = Field(default=None, foreign_key="prediction.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ModelMetrics(SQLModel, table=True):
    """สถิติประสิทธิภาพของโมเดล (อัพเดทหลัง retrain)"""
    id: Optional[int] = Field(default=None, primary_key=True)
    recorded_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    model_version: str
    total_trades: int = Field(default=0)
    win_trades: int = Field(default=0)
    loss_trades: int = Field(default=0)
    win_rate: float = Field(default=0.0)
    total_profit: float = Field(default=0.0)
    profit_factor: float = Field(default=0.0)
    sharpe_ratio: float = Field(default=0.0)
    max_drawdown: float = Field(default=0.0)
    avg_rr: float = Field(default=0.0)
    final_equity: float = Field(default=10000.0)
    eval_reward: float = Field(default=0.0)
    notes: Optional[str] = None


class TrainingLog(SQLModel, table=True):
    """Log การ train โมเดล"""
    id: Optional[int] = Field(default=None, primary_key=True)
    started_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    finished_at: Optional[datetime] = None
    model_version: str
    status: str = Field(default="RUNNING")            # RUNNING / SUCCESS / FAILED
    timesteps: int = Field(default=0)
    best_reward: float = Field(default=0.0)
    train_data_start: Optional[datetime] = None
    train_data_end: Optional[datetime] = None
    error_message: Optional[str] = None
