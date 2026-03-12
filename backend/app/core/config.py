from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Twelve Data — ดึง XAU/USD hourly (free: 800 credits/day)
    # สมัคร: https://twelvedata.com/register
    twelve_data_api_key: str = "demo"

    # FRED (St. Louis Fed) — ดึง WTI oil daily (ฟรี 100% ไม่ต้องมี key)
    # key optional ช่วยเพิ่ม rate limit: https://fred.stlouisfed.org/docs/api/api_key.html

    # Database
    database_url: str = "sqlite:///./database/gold_trading.db"

    # Model
    # +Oil model: use_oil=True, use_rsi=False, use_macd=False, use_sr=False, use_trend=True
    # obs_dim = 5 (OHLCV) + 5 (trend regime) + 1 (oil) + 3 (account) = 14
    model_path:    str = "./RL_model/best_model_ppo_1M_oil_medRisk_noSeed.zip"
    model_version: str = "oil_1M"
    model_obs_dim: int = 14

    # Seed data paths (โหลดข้อมูลเริ่มต้นตอน startup)
    seed_gold_csv: str = "./data/XAU_1h_data.csv"
    seed_oil_csv:  str = "./data/crude-oil-price.csv"

    # Scheduler
    price_fetch_interval_hours: int = 1
    predict_interval_hours:     int = 1
    retrain_interval_days:      int = 30

    # App
    debug:        bool       = False
    cors_origins: list[str]  = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://frontend:3000",
    ]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        frozen = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
