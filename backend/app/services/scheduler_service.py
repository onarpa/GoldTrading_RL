"""
Scheduler Service
=================
APScheduler สำหรับ:
  - ดึงราคาทุก 1 ชั่วโมง (:00)
  - ตรวจ open trades ทันทีหลังดึงราคา (:02) ← เพิ่มใหม่
  - predict ทุก 1 ชั่วโมง (:05)
  - retrain ทุก 30 วัน
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import logging
from datetime import datetime

from database.database import get_session
from app.services.price_service import fetch_and_save_gold, fetch_and_save_oil
from app.services.model_service import predict_and_save, check_open_trades
from app.services.training_service import retrain_model

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler(timezone='UTC')


async def job_fetch_prices():
    """Job: ดึงราคาทองคำและน้ำมันทุกชั่วโมง (:00)"""
    logger.info(f"[Scheduler] Fetching prices at {datetime.utcnow().isoformat()}")
    with next(get_session()) as session:
        try:
            gold_count = await fetch_and_save_gold(session)
            oil_count  = await fetch_and_save_oil(session)
            logger.info(f"[Scheduler] Fetched gold={gold_count}, oil={oil_count} rows")
        except Exception as e:
            logger.error(f"[Scheduler] Price fetch error: {e}")


async def job_check_trades():
    """
    Job: ตรวจ open trades ทันทีหลังดึงราคา (:02)

    เหตุผล: _check_open_trades เดิมรันแค่ตอน predict (:05)
            ถ้า TP/SL ถูก hit ใน bar ที่เพิ่งดึงมา (:00)
            trade จะไม่ปิดจนกว่า predict รอบถัดไป (อีก 1 ชั่วโมง)
            job นี้แก้โดยรัน check ที่ :02 ทันทีหลังดึงราคา
    """
    logger.info(f"[Scheduler] Checking open trades at {datetime.utcnow().isoformat()}")
    with next(get_session()) as session:
        try:
            closed = check_open_trades(session)
            if closed:
                logger.info(f"[Scheduler] Auto-closed {closed} trade(s)")
        except Exception as e:
            logger.error(f"[Scheduler] Trade check error: {e}")


async def job_predict():
    """Job: predict ทุกชั่วโมง (:05) — หลัง fetch prices + trade check"""
    logger.info(f"[Scheduler] Running prediction at {datetime.utcnow().isoformat()}")
    with next(get_session()) as session:
        try:
            pred = await predict_and_save(session)
            if pred:
                logger.info(f"[Scheduler] Prediction: {pred.action} @ {pred.gold_price:.2f}")
        except Exception as e:
            logger.error(f"[Scheduler] Prediction error: {e}")


async def job_monthly_retrain():
    """Job: retrain model ทุกเดือน (วันที่ 1 เวลา 02:00 UTC)"""
    logger.info(f"[Scheduler] Starting monthly retrain at {datetime.utcnow().isoformat()}")
    with next(get_session()) as session:
        try:
            result = await retrain_model(session, force=False)
            logger.info(f"[Scheduler] Retrain result: {result}")
        except Exception as e:
            logger.error(f"[Scheduler] Retrain error: {e}")


def start_scheduler():
    # :00 — ดึงราคา
    scheduler.add_job(job_fetch_prices,  CronTrigger(minute=0),          id="fetch_prices",    replace_existing=True)
    # :02 — ตรวจ open trades ทันที (FIX: เพิ่มใหม่)
    scheduler.add_job(job_check_trades,  CronTrigger(minute=2),          id="check_trades",    replace_existing=True)
    # :05 — predict (ซึ่งก็จะ check trades อีกรอบหลัง predict)
    scheduler.add_job(job_predict,       CronTrigger(minute=5),          id="predict",         replace_existing=True)
    # วันที่ 1 02:00 — retrain
    scheduler.add_job(job_monthly_retrain, CronTrigger(day=1, hour=2, minute=0), id="monthly_retrain", replace_existing=True)

    scheduler.start()
    logger.info("Scheduler started: fetch@:00, check_trades@:02, predict@:05, retrain monthly")


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler stopped")
