# Gold Trading RL System — v23

ระบบวิเคราะห์และจำลองการซื้อขายทองคำ (XAU/USD) ด้วย Reinforcement Learning  
ใช้อัลกอริทึม **PPO + WTI Oil feature** ผ่าน Web Application แบบ Real-time

---

## สถาปัตยกรรมระบบ

```
tradingSimulation/
├── backend/
│   ├── app/
│   │   ├── controllers/          HTTP endpoints (FastAPI)
│   │   │   ├── price_controller.py
│   │   │   ├── prediction_controller.py
│   │   │   └── frontend_controller.py
│   │   ├── services/             Business logic
│   │   │   ├── price_service.py         ดึงราคา + seed CSV + indicators
│   │   │   ├── model_service.py         PPO predict + trade management
│   │   │   ├── scheduler_service.py     APScheduler jobs
│   │   │   └── training_service.py      Monthly retrain
│   │   └── core/config.py
│   ├── database/
│   │   ├── models.py             SQLModel table definitions
│   │   ├── database.py           SQLite engine
│   │   └── crud.py               DB operations
│   ├── RL_model/
│   │   ├── best_model_ppo_1M_oil_medRisk_noSeed.zip   (โมเดลหลัก)
│   │   └── trading_env.py                             Gymnasium environment
│   └── data/
│       ├── XAU_1h_data.csv        ข้อมูลราคาทองย้อนหลัง 2005-2025 (seed)
│       └── crude-oil-price.csv    ข้อมูลราคาน้ำมัน WTI (seed)
├── frontend/                     React + Vite + Tailwind CSS
└── docker-compose.yml
```

---

## โมเดล (+Oil Config)

| Parameter              | Value                                        |
|------------------------|----------------------------------------------|
| Model file             | best_model_ppo_1M_oil_medRisk_noSeed.zip     |
| Algorithm              | PPO (Proximal Policy Optimization)           |
| Policy                 | MlpPolicy (256×256)                          |
| obs_dim                | 14                                           |
| use_oil_price          | True                                         |
| use_trend_regime       | True                                         |
| use_rsi / macd / s_r   | False                                        |
| Training data          | XAU/USD 1h, 2005–2022 (train) / 2023 (val)  |
| Timesteps              | 1,000,000                                    |

### Observation Vector (14 มิติ)

| Index | Feature                     | Scaling                    |
|-------|-----------------------------|----------------------------|
| 0     | Open                        | MinMaxScaler (fit on DB)   |
| 1     | High                        | MinMaxScaler (fit on DB)   |
| 2     | Low                         | MinMaxScaler (fit on DB)   |
| 3     | Close                       | MinMaxScaler (fit on DB)   |
| 4     | Volume                      | MinMaxScaler (fit on DB)   |
| 5     | (close − EMA50) / close     | —                          |
| 6     | (close − EMA200) / close    | —                          |
| 7     | (EMA50 − EMA200) / close    | —                          |
| 8     | EMA50 slope (24 bar)        | —                          |
| 9     | EMA200 slope (24 bar)       | —                          |
| 10    | WTI Oil price               | StandardScaler (μ=71.87)   |
| 11    | balance / initial_balance   | = 1.0 (fixed)              |
| 12    | equity  / initial_balance   | = 1.0 (fixed)              |
| 13    | open_orders / max_orders    | = 0.0 (fixed)              |

---

## API Keys ที่ต้องใช้

ระบบใช้ **AlphaVantage API** แยก 2 key เพื่อหลีกเลี่ยง rate limit (free tier: 25 req/day)

| Key                           | ใช้สำหรับ           |
|-------------------------------|---------------------|
| ALPHA_VANTAGE_API_KEY_GOLD    | XAU/USD hourly      |
| ALPHA_VANTAGE_API_KEY_OIL     | WTI crude oil daily |

สมัครฟรี: https://www.alphavantage.co/support/#api-key

---

## Quick Start

### 1. ตั้งค่า API Keys

แก้ไฟล์ `.env` ที่ root:

```env
ALPHA_VANTAGE_API_KEY_GOLD=YOUR_GOLD_KEY
ALPHA_VANTAGE_API_KEY_OIL=YOUR_OIL_KEY
```

### 2. รันด้วย Docker (แนะนำ)

```bash
docker-compose up --build
```

| Service     | URL                         |
|-------------|------------------------------|
| Frontend    | http://localhost:3000        |
| Backend API | http://localhost:8000        |
| Swagger UI  | http://localhost:8000/docs   |

ตอน startup ระบบจะ seed ข้อมูลจาก CSV อัตโนมัติ (~2–3 นาที สำหรับ 124k rows)

### 3. รันโดยไม่ใช้ Docker

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend (terminal แยก)
cd frontend
npm install
npm run dev
```

---

## Scheduler Jobs

| Job              | เวลา (UTC)                  | หน้าที่                                      |
|------------------|-----------------------------|----------------------------------------------|
| fetch_prices     | ทุกชั่วโมง :00              | ดึง XAU/USD + WTI จาก AlphaVantage           |
| check_trades     | ทุกชั่วโมง :02              | ตรวจ TP/SL ทุก bar ตั้งแต่เปิด trade (FIX)  |
| predict          | ทุกชั่วโมง :05              | รัน RL model → บันทึก prediction + trade      |
| monthly_retrain  | วันที่ 1 ของเดือน 02:00     | Retrain PPO จากข้อมูลใน DB                   |

> **หมายเหตุ `check_trades`:** job นี้เพิ่มใน v23 เพื่อแก้บัค trade ไม่ปิด  
> ดูรายละเอียดใน [CHANGELOG](#changelog)

---

## API Endpoints

### Prices
```
POST /api/prices/fetch              ดึงราคาทันที
GET  /api/prices/gold/latest        ราคา gold ล่าสุด
GET  /api/prices/gold/history       ประวัติราคา N ชั่วโมง
GET  /api/prices/oil/latest         ราคา oil ล่าสุด
```

### Predictions
```
POST /api/predictions/predict       predict ทันที (ไม่เปิด trade)
GET  /api/predictions/latest        prediction ล่าสุด
GET  /api/predictions/history       ประวัติ predictions
GET  /api/predictions/trades        trade log + สรุป
```

### Frontend Aggregates
```
GET  /api/dashboard                 ข้อมูล Dashboard
GET  /api/performance               Model Performance
GET  /api/visualization             Indicator charts
POST /api/model/train               Trigger retraining
GET  /api/model/training-logs       Training history
```

---

## Database Tables

| Table          | Content                                    |
|----------------|--------------------------------------------|
| goldprice      | ราคาทองคำรายชั่วโมง + EMA/RSI/MACD/BB     |
| oilprice       | ราคาน้ำมัน WTI รายชั่วโมง                 |
| prediction     | ผล predict จาก RL model (1 รายการ/ชั่วโมง)|
| trade          | Simulated trades พร้อม TP/SL tracking      |
| modelmetrics   | สถิติประสิทธิภาพโมเดล                      |
| traininglog    | ประวัติการ retrain                          |

---

## CHANGELOG

### v23
- **FIX: Trade ไม่ปิดเมื่อ TP/SL ถูก hit**
  - `check_open_trades()` เดิมตรวจแค่ bar เดียว (latest)
  - แก้เป็น scan ทุก bar ตั้งแต่ `trade.open_time` เรียงตามลำดับเวลา
  - ปิด trade ที่ bar แรกที่ hit TP หรือ SL
  - เพิ่ม scheduler job `check_trades` ที่ :02 (หลัง fetch ราคา)
  - `check_open_trades` ถูก export เป็น public function ให้ scheduler เรียกได้

### v22
- Dashboard chart auto-update ทุก 2 นาที
- ราคา real-time ไม่ delay (แก้ end_date=now_utc)
- Volume fallback median เมื่อ volume=0

### v17
- Initial stable release
