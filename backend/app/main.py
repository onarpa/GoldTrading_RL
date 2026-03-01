from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.services.data_fetcher import fetch_historical_data
from app.services.indicators import add_technical_indicators
from datetime import datetime, timedelta
import pandas as pd
import math

app = FastAPI(title="Gold Trading API")

# ตั้งค่า CORS เพื่ออนุญาตให้ React (พอร์ต 5173) สามารถดึงข้อมูลจาก FastAPI ได้
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # อนุญาตทุก Port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to Gold Price Trend Analysis API"}

@app.get("/api/dashboard-data")
def get_dashboard_data():
    try:
        # ดึงข้อมูลย้อนหลัง 60 วัน (เผื่อวันหยุดและเพื่อให้ EMA/MACD มีข้อมูลพอคำนวณ)
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")
        
        # 1. ดึงข้อมูลและคำนวณ Indicator
        raw_df = fetch_historical_data(start_date=start_date, end_date=end_date)
        df = add_technical_indicators(raw_df)
        
        # 2. คัดลอกเฉพาะ 30 วันล่าสุดส่งให้เว็บ
        recent_df = df.tail(30).copy()
        
        # รีเซ็ต Index เพื่อเอาคอลัมน์ Date ออกมา และแปลงค่า NaN เป็น 0 ป้องกัน JSON Error
        recent_df.reset_index(inplace=True)
        recent_df['Date'] = recent_df['Date'].astype(str)
        recent_df.fillna(0, inplace=True)
        
        # 3. แปลง DataFrame เป็น List of Dictionaries
        data_records = recent_df.to_dict(orient="records")
        
        if len(data_records) < 2:
            return {"status": "error", "message": "ข้อมูลไม่เพียงพอ"}

        # 4. ดึงข้อมูลล่าสุด (วันนี้) และเมื่อวานเพื่อหาการเปลี่ยนแปลง
        latest = data_records[-1]
        previous = data_records[-2]
        
        price_change = latest['Close'] - previous['Close']
        percent_change = (price_change / previous['Close']) * 100
        
        # จำลองคำแนะนำเบื้องต้น (เดี๋ยวเราจะเอา AI มาแทนที่ตรงนี้ในอนาคต)
        recommend = "HOLD"
        if latest['MACD'] > latest['MACD_Signal'] and latest['RSI'] < 70:
            recommend = "BUY"
        elif latest['MACD'] < latest['MACD_Signal'] and latest['RSI'] > 30:
            recommend = "SELL"
            
        # สร้าง Response ส่งกลับไปให้ React
        return {
            "status": "success",
            "current_price": round(latest['Close'], 2),
            "price_change": round(price_change, 2),
            "percent_change": round(percent_change, 2),
            "recommendation": recommend,
            "technical": {
                "rsi": round(latest['RSI'], 2),
                "macd": round(latest['MACD'], 2),
                "ema_20": round(latest['EMA_20'], 2)
            },
            "chart_data": [round(record['Close'], 2) for record in data_records],
            "chart_labels": [record['Date'] for record in data_records]
        }
        
    except Exception as e:
        return {"status": "error", "message": str(e)}