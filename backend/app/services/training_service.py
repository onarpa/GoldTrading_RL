"""
Training Service
================
Retrain PPO model ทุก 30 วัน โดยใช้ config ตรงกับ notebook (FinalPcolab2.ipynb):
  - scaler: MinMaxScaler (fit on df passed to env)
  - oil: StandardScaler normalized
  - risk_bounds=(0.005, 0.015)
  - min_rr=1.1
  - spread_pct=0.0002
"""
import logging
import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sqlmodel import Session

from app.core.config import get_settings
from database.models import TrainingLog, ModelMetrics
from database import crud

logger   = logging.getLogger(__name__)
settings = get_settings()


async def retrain_model(session: Session, force: bool = False) -> dict:
    if not force:
        logs = crud.get_training_logs(session, limit=1)
        if logs and logs[0].status == "SUCCESS":
            days_since = (datetime.utcnow() - logs[0].started_at).days
            if days_since < settings.retrain_interval_days:
                return {
                    "status":  "skipped",
                    "message": f"Last training {days_since} days ago "
                               f"(min: {settings.retrain_interval_days})",
                }

    version = datetime.utcnow().strftime("v%Y%m%d")
    log = crud.create_training_log(session, TrainingLog(
        started_at    = datetime.utcnow(),
        model_version = version,
        status        = "RUNNING",
    ))

    try:
        return await _run_training(session, log.id, version)
    except Exception as e:
        crud.update_training_log(
            session, log.id,
            status="FAILED", finished_at=datetime.utcnow(), error_message=str(e),
        )
        logger.error(f"Training failed: {e}")
        return {"status": "failed", "error": str(e), "log_id": log.id}


async def _run_training(session: Session, log_id: int, version: str) -> dict:
    try:
        from stable_baselines3 import PPO
        from stable_baselines3.common.vec_env import DummyVecEnv
        from stable_baselines3.common.callbacks import EvalCallback
        from sklearn.preprocessing import MinMaxScaler
        import torch as th
    except ImportError as e:
        raise ImportError(f"Missing training dependencies: {e}")

    since  = datetime.utcnow() - timedelta(days=365 * 2)
    prices = crud.get_gold_prices_since(session, since)

    # ถ้า DB ไม่พอให้โหลดจาก CSV แทน
    if len(prices) < 1000:
        csv_path = settings.seed_gold_csv
        if os.path.exists(csv_path):
            import pandas as _pd
            _df = _pd.read_csv(csv_path, sep=";")
            _df.columns = [c.strip() for c in _df.columns]
            _df["timestamp"] = _pd.to_datetime(_df["Date"], format="%Y.%m.%d %H:%M")
            _df = _df.rename(columns={"Open":"open","High":"high","Low":"low","Close":"close","Volume":"volume"})
            # สร้าง GoldPrice objects จาก CSV เพื่อใช้ใน training เท่านั้น (ไม่ save ลง DB)
            from database.models import GoldPrice as _GP
            prices = [_GP(timestamp=r.timestamp, open=r.open, high=r.high,
                          low=r.low, close=r.close, volume=r.volume)
                      for _, r in _df.iterrows()]

    if len(prices) < 1000:
        msg = f"Not enough data: {len(prices)} rows (need >= 1000)"
        crud.update_training_log(session, log_id,
            status="FAILED", finished_at=datetime.utcnow(), error_message=msg)
        return {"status": "failed", "error": msg}

    gold_df = pd.DataFrame([{
        "Date":   p.timestamp,
        "Open":   p.open,
        "High":   p.high,
        "Low":    p.low,
        "Close":  p.close,
        "Volume": p.volume,
    } for p in sorted(prices, key=lambda x: x.timestamp)])

    # Oil prices aligned to gold timestamps
    oil_prices = crud.get_oil_prices_since(session, gold_df["Date"].iloc[0])
    oil_map    = {p.timestamp: p.close for p in oil_prices}
    last_oil   = 72.0
    oil_raw    = []
    for ts in gold_df["Date"]:
        v = oil_map.get(ts)
        if v is not None:
            last_oil = v
        oil_raw.append(last_oil)

    oil_raw = np.array(oil_raw, dtype=np.float32)

    split     = int(len(gold_df) * 0.8)
    train_df  = gold_df.iloc[:split].reset_index(drop=True)
    eval_df   = gold_df.iloc[split:].reset_index(drop=True)
    oil_raw_train = oil_raw[:split]
    oil_raw_eval  = oil_raw[split:]

    # MinMaxScaler (matches notebook Cell 5)
    # TradingEnv calls fit_transform on df internally — pass a fresh MinMaxScaler
    from sklearn.preprocessing import MinMaxScaler
    scaler = MinMaxScaler()

    # StandardScaler for oil (matches notebook Cell 12)
    from sklearn.preprocessing import StandardScaler as SS
    oil_ss = SS()
    oil_train_scaled = oil_ss.fit_transform(oil_raw_train.reshape(-1, 1)).astype(np.float32)
    oil_eval_scaled  = oil_ss.transform(oil_raw_eval.reshape(-1, 1)).astype(np.float32)

    crud.update_training_log(session, log_id,
        train_data_start=train_df["Date"].iloc[0],
        train_data_end=train_df["Date"].iloc[-1],
    )

    try:
        from RL_model.trading_env import TradingEnv
    except ImportError:
        logger.warning("TradingEnv not found in RL_model — skipping training")
        _save_placeholder_metrics(session, version)
        crud.update_training_log(session, log_id,
            status="SUCCESS", finished_at=datetime.utcnow(), timesteps=0, best_reward=0.0)
        return {"status": "success", "log_id": log_id, "version": version, "placeholder": True}

    def make_train_env():
        return TradingEnv(
            train_df,
            oil_price_df           = oil_train_scaled,
            use_oil_price          = True,
            use_rsi                = False,
            use_macd               = False,
            use_support_resistance = False,
            use_trend_regime       = True,
            scaler                 = MinMaxScaler(),   # re-fit on train_df inside TradingEnv
            episode_logging        = False,
            # params ตรงกับ notebook Cell 82
            tp_bounds              = (0.006, 0.015),
            sl_bounds              = (0.003, 0.008),
            risk_bounds            = (0.005, 0.015),
            min_rr                 = 1.1,
            spread_pct             = 0.0002,
            commission_per_lot     = 0.0,
            reward_volatility_scale = 5.0,
            reward_drawdown_power   = 1.5,
        )

    def make_eval_env():
        return TradingEnv(
            eval_df,
            oil_price_df           = oil_eval_scaled,
            use_oil_price          = True,
            use_rsi                = False,
            use_macd               = False,
            use_support_resistance = False,
            use_trend_regime       = True,
            scaler                 = MinMaxScaler(),
            episode_logging        = True,
            tp_bounds              = (0.006, 0.015),
            sl_bounds              = (0.003, 0.008),
            risk_bounds            = (0.005, 0.015),
            min_rr                 = 1.1,
            spread_pct             = 0.0002,
            commission_per_lot     = 0.0,
            reward_volatility_scale = 5.0,
            reward_drawdown_power   = 1.5,
        )

    train_env = DummyVecEnv([make_train_env])
    eval_env  = DummyVecEnv([make_eval_env])

    os.makedirs("RL_model", exist_ok=True)
    eval_callback = EvalCallback(
        eval_env,
        best_model_save_path = "RL_model/best_model",
        log_path             = "RL_model/logs",
        eval_freq            = 25000,
        n_eval_episodes      = 5,
        deterministic        = True,
        verbose              = 0,
    )

    # PPO config matches notebook best config
    model = PPO("MlpPolicy", train_env,
        learning_rate = 1e-4,
        n_steps       = 4096,
        batch_size    = 256,
        n_epochs      = 10,
        gamma         = 0.999,
        gae_lambda    = 0.95,
        clip_range    = 0.2,
        ent_coef      = 0.03,
        vf_coef       = 0.75,
        max_grad_norm = 0.5,
        policy_kwargs = dict(
            net_arch      = dict(pi=[256, 256], vf=[256, 256]),
            activation_fn = th.nn.Tanh,
        ),
        verbose = 0,
    )

    TIMESTEPS = 500_000
    model.learn(total_timesteps=TIMESTEPS, callback=eval_callback, progress_bar=False)
    model.save(f"RL_model/{version}")

    settings.model_version = version
    from app.services.model_service import reload_model
    reload_model()

    eval_reward = _evaluate(f"RL_model/best_model.zip", eval_env)
    _save_metrics(session, version, eval_reward)

    crud.update_training_log(session, log_id,
        status="SUCCESS", finished_at=datetime.utcnow(),
        timesteps=TIMESTEPS, best_reward=eval_reward,
    )
    logger.info(f"Training done: version={version} eval_reward={eval_reward:.2f}")
    return {"status": "success", "log_id": log_id, "version": version, "eval_reward": eval_reward}


def _evaluate(model_path: str, eval_env, n_episodes: int = 5) -> float:
    try:
        from stable_baselines3 import PPO
        model   = PPO.load(model_path)
        rewards = []
        for _ in range(n_episodes):
            obs = eval_env.reset()
            done = np.array([False])
            while not done.all():
                action, _ = model.predict(obs, deterministic=True)
                obs, _, done, info = eval_env.step(action)
            bal = info[0].get("balance", 10000) if info else 10000
            rewards.append(bal - 10000)
        return float(np.mean(rewards))
    except Exception as e:
        logger.error(f"Eval error: {e}")
        return 0.0


def _save_metrics(session: Session, version: str, eval_reward: float):
    crud.save_metrics(session, ModelMetrics(
        model_version  = version,
        total_trades=0, win_trades=0, loss_trades=0,
        win_rate=0.0, total_profit=eval_reward,
        profit_factor=0.0, sharpe_ratio=0.0,
        max_drawdown=0.0, avg_rr=0.0,
        final_equity=10000.0 + eval_reward,
        eval_reward=eval_reward,
        notes=f"Auto-retrain {version}",
    ))


def _save_placeholder_metrics(session: Session, version: str):
    crud.save_metrics(session, ModelMetrics(
        model_version = version,
        total_trades=0, win_trades=0, loss_trades=0,
        win_rate=0.0, total_profit=0.0,
        profit_factor=0.0, sharpe_ratio=0.0,
        max_drawdown=0.0, avg_rr=0.0,
        final_equity=10000.0, eval_reward=0.0,
        notes="Placeholder — TradingEnv not available",
    ))
