import logging
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from database.database import create_db_and_tables, get_session
from app.core.config import get_settings
from app.controllers.price_controller import router as price_router
from app.controllers.prediction_controller import router as prediction_router
from app.controllers.frontend_controller import router as frontend_router
from app.services.scheduler_service import start_scheduler, stop_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger   = logging.getLogger(__name__)
settings = get_settings()


async def _seed_initial_data():
    """Seed 500 bars จาก Twelve Data API — fallback ไป CSV ถ้าไม่มี key"""
    from app.services.price_service import seed_gold_from_api, seed_oil_from_csv, _compute_and_update_indicators
    with next(get_session()) as session:
        try:
            gold_rows = await seed_gold_from_api(session)
            oil_rows  = seed_oil_from_csv(session)
            if gold_rows > 0 or oil_rows > 0:
                logger.info(f"Seed complete: gold={gold_rows} oil={oil_rows} rows")
            # รัน compute indicators เสมอ — รองรับ DB เดิมที่ขาด bb_*/ema_*
            logger.info("Recomputing indicators on latest 500 bars ...")
            _compute_and_update_indicators(session)
            logger.info("Indicators updated.")
        except Exception as e:
            logger.error(f"Seed error: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Gold Trading API ...")
    create_db_and_tables()
    # โหลด seed data ใน background task (ไม่รอให้เสร็จก่อน serve)
    asyncio.create_task(_seed_initial_data())
    start_scheduler()
    logger.info("API ready.")
    yield
    stop_scheduler()
    logger.info("Shutdown complete.")


app = FastAPI(
    title       = "Gold Trading RL API",
    description = "ระบบวิเคราะห์แนวโน้มราคาทองคำด้วย Reinforcement Learning (+Oil model)",
    version     = "2.1.0",
    lifespan    = lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins     = settings.cors_origins + ["*"],
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)

app.include_router(price_router)
app.include_router(prediction_router)
app.include_router(frontend_router)


@app.get("/")
def root():
    return {"message": "Gold Trading RL API", "version": "2.1.0", "docs": "/docs"}


@app.get("/health")
def health():
    import datetime
    return {"status": "ok", "timestamp": datetime.datetime.utcnow().isoformat()}
