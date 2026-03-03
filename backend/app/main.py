from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.services.data_fetcher import fetch_historical_data
from app.services.indicators import add_technical_indicators
from datetime import datetime, timedelta
import random
import numpy as np
import pandas as pd

app = FastAPI(title="Gold Trading API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # อนุญาตทุก Port ป้องกันเว็บค้าง
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/dashboard-data")
def get_dashboard_data():
    try:
        # ดึงข้อมูลย้อนหลัง 1 ปีก็พอสำหรับหน้าเว็บ (เพื่อไม่ให้โหลดช้าเกินไป)
        # ส่วน AI ค่อยให้มันดึง 20 ปี ตอน train
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        
        # ดึงข้อมูลและคำนวณ Indicator (ของจริง)
        raw_df = fetch_historical_data(start_date=start_date, end_date=end_date)
        df = add_technical_indicators(raw_df)
        
        # คัดเอาเฉพาะ 30 วันทำการล่าสุดมาแสดงบนกราฟหน้าเว็บ
        recent_df = df.tail(30).copy()
        recent_df.reset_index(inplace=True)
        recent_df['Date'] = recent_df['Date'].astype(str)
        recent_df.fillna(0, inplace=True)
        
        # แปลงข้อมูลให้อยู่ในรูปแบบ List ที่ส่งผ่านเว็บได้
        data_records = recent_df.to_dict(orient="records")
        latest = data_records[-1]
        previous = data_records[-2]
        
        if len(data_records) < 2:
            return {"status": "error", "message": "ข้อมูลไม่เพียงพอ"}

        # ดึงข้อมูลวันล่าสุด (วันนี้) และเมื่อวานเพื่อหาความเปลี่ยนแปลง
        latest = data_records[-1]
        previous = data_records[-2]
        
        # คำนวณความเปลี่ยนแปลงทองคำ
        price_change = latest['Close'] - previous['Close']
        percent_change = (price_change / previous['Close']) * 100
        
        # คำนวณความเปลี่ยนแปลงน้ำมัน
        oil_change = latest['Oil_Price'] - previous['Oil_Price']
        oil_percent = (oil_change / previous['Oil_Price']) * 100
        
        # ระบบแนะนำเบื้องต้นตาม Indicator (ก่อนที่ AI จะมาแทนที่)
        recommend = "HOLD"
        if latest['MACD'] > latest['MACD_Signal'] and latest['RSI'] < 70:
            recommend = "BUY"
        elif latest['MACD'] < latest['MACD_Signal'] and latest['RSI'] > 30:
            recommend = "SELL"

        # --- คำนวณสถิติสำคัญจากข้อมูลจริง (Pandas) ---
        # ราคาสูงสุด-ต่ำสุดในรอบ 1 ปี (52 สัปดาห์)
        high_52w = df['High'].max()
        low_52w = df['Low'].min()

        # ค่าเฉลี่ย 30 วันทำการล่าสุด
        avg_30d = recent_df['Close'].mean()

        # ความผันผวน 30 วัน (คำนวณจากกรอบการแกว่งตัว: (ราคาสูงสุด 30 วัน - ราคาต่ำสุด 30 วัน) / ราคาต่ำสุด * 100)
        vol_30d = ((recent_df['High'].max() - recent_df['Low'].min()) / recent_df['Low'].min()) * 100
            
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
            "oil": {
                "price": round(latest['Oil_Price'], 2),
                "change": round(oil_change, 2),
                "percent": round(oil_percent, 2)
            },
            "statistics": {
                "high_52w": round(high_52w, 2),
                "low_52w": round(low_52w, 2),
                "avg_30d": round(avg_30d, 2),
                "volatility_30d": round(vol_30d, 2)
            },
            "chart_data": [round(record['Close'], 2) for record in data_records], # แกน Y: ราคาปิด 30 วัน
            "chart_labels": [record['Date'] for record in data_records] # แกน X: วันที่ 30 วัน
        }
        
    except Exception as e:
        return {"status": "error", "message": str(e)}
    
# PredictionResult.jsx
    
@app.get("/api/model-performance")
def get_model_performance():
    try:
        # 1. จำลองข้อมูลกราฟ Cumulative Return (ผลตอบแทนสะสมย้อนหลัง 60 วัน)
        cumulative_data = []
        cum_return = 0
        base_date = datetime.now() - timedelta(days=60)
        
        for i in range(60):
            date_str = (base_date + timedelta(days=i)).strftime("%Y-%m-%d")
            # สมมติให้ AI ทำกำไรเฉลี่ยวันละนิดหน่อย (มีบวกมีลบสลับกัน)
            daily_return = random.uniform(-1.2, 1.5) 
            cum_return += daily_return
            cumulative_data.append({"date": date_str, "value": round(cum_return, 2)})

        # 2. จำลองข้อมูลตารางสถิติรายเดือน (ย้อนหลัง 6 เดือน)
        months = ["ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.", "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."]
        current_month_idx = datetime.now().month - 1
        
        monthly_data = []
        total_trades = 0
        winning_trades = 0

        for i in range(6):
            m_idx = (current_month_idx - 5 + i) % 12
            month_name = f"{months[m_idx]} {(datetime.now().year if m_idx <= current_month_idx else datetime.now().year - 1)}"
            
            # สุ่มจำนวนการเทรดและอัตราการชนะในเดือนนั้นๆ
            trades = random.randint(12, 25)
            win_trades = int(trades * random.uniform(0.60, 0.80)) # ชนะประมาณ 60-80%
            
            total_trades += trades
            winning_trades += win_trades
            
            m_return = random.uniform(-2.0, 7.5) # ผลตอบแทนรายเดือน
            m_accuracy = (win_trades / trades) * 100
            
            monthly_data.append({
                "month": month_name,
                "return": round(m_return, 2),
                "accuracy": round(m_accuracy, 2),
                "win_rate": round(m_accuracy - random.uniform(0.5, 2.0), 2),
                "trades": trades
            })

        # 3. คำนวณสถิติภาพรวม (Overall Metrics)
        overall_accuracy = (winning_trades / total_trades) * 100
        
        return {
            "status": "success",
            "metrics": {
                "accuracy": round(overall_accuracy, 2),
                "sharpe_ratio": round(random.uniform(1.5, 2.2), 2), # Sharpe > 1 ถือว่าดีมาก
                "win_rate": round(overall_accuracy - 1.5, 2),
                "max_drawdown": round(random.uniform(-5.0, -12.0), 2) # ติดลบสูงสุด
            },
            "cumulative_chart": {
                "labels": [d["date"] for d in cumulative_data],
                "data": [d["value"] for d in cumulative_data]
            },
            "monthly_chart": {
                "labels": [d["month"] for d in monthly_data],
                "data": [d["return"] for d in monthly_data]
            },
            # พลิกข้อมูลให้เดือนล่าสุดอยู่ด้านบนของตาราง
            "table_data": monthly_data[::-1] 
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/data-visualization")
def get_data_visualization():
    try:
        # 1. ดึงข้อมูล 1 ปี เพื่อให้คำนวณ Indicator ได้แม่นยำ 
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        
        raw_df = fetch_historical_data(start_date=start_date, end_date=end_date)
        df = add_technical_indicators(raw_df)
        
        # 2. คัดเอาเฉพาะ 20 วันทำการล่าสุดมาทำกราฟ
        recent_df = df.tail(20).copy()
        recent_df.reset_index(inplace=True)
        recent_df['Date'] = recent_df['Date'].astype(str)
        recent_df.fillna(0, inplace=True)
        
        data_records = recent_df.to_dict(orient="records")
        latest = data_records[-1]

        # 3. สร้างข้อมูลสำหรับการวิเคราะห์ (Analysis Logic)
        
        # Moving Average Analysis 
        ma_analysis = {
            "title": "Moving Average",
            "value_text": f"ราคาอยู่{'เหนือ' if latest['Close'] > latest['EMA_20'] else 'ใต้'} MA20",
            "signal": "สัญญาณขาขึ้น" if latest['Close'] > latest['EMA_20'] and latest['Close'] > latest['EMA_50'] else ("สัญญาณขาลง" if latest['Close'] < latest['EMA_20'] and latest['Close'] < latest['EMA_50'] else "รอความชัดเจน"),
            "color_theme": "green" if latest['Close'] > latest['EMA_20'] else "red"
        }

        # RSI Analysis 
        rsi_val = latest['RSI']
        rsi_zone = "อยู่ในเขตกลาง"
        rsi_signal = "รอความชัดเจน"
        rsi_color = "yellow"
        if rsi_val > 70:
            rsi_zone = "Overbought (ซื้อมากเกินไป)"
            rsi_signal = "สัญญาณระวังขาย"
            rsi_color = "red"
        elif rsi_val < 30:
            rsi_zone = "Oversold (ขายมากเกินไป)"
            rsi_signal = "สัญญาณระวังซื้อ"
            rsi_color = "green"

        rsi_analysis = {
            "title": "RSI",
            "value_text": f"RSI = {round(rsi_val, 1)}",
            "signal": rsi_zone,
            "color_theme": rsi_color
        }

        # MACD Analysis
        macd_val = latest['MACD']
        macd_signal_line = latest['MACD_Signal']
        
        macd_analysis = {
            "title": "MACD",
            "value_text": f"MACD {'เหนือ' if macd_val > macd_signal_line else 'ใต้'} Signal Line",
            "signal": "สัญญาณบวก" if macd_val > macd_signal_line else "สัญญาณลบ",
            "color_theme": "blue" if macd_val > macd_signal_line else "red"
        }

        return {
            "status": "success",
            "labels": [record['Date'] for record in data_records],
            "price_data": [round(record['Close'], 2) for record in data_records],
            
            # Indicator Data
            "ma_data": {
                "ma20": [round(record['EMA_20'], 2) for record in data_records],
                "ma50": [round(record['EMA_50'], 2) for record in data_records] # เพิ่ม MA50 เข้าไปด้วยถ้าต้องการ
            },
            "rsi_data": [round(record['RSI'], 2) for record in data_records],
            "macd_data": {
                "macd": [round(record['MACD'], 2) for record in data_records],
                "signal": [round(record['MACD_Signal'], 2) for record in data_records]
            },
            "bb_data": {
                "upper": [round(record['BB_High'], 2) for record in data_records],
                "lower": [round(record['BB_Low'], 2) for record in data_records]
            },
            
            # Analysis Summary
            "analysis": {
                "ma": ma_analysis,
                "rsi": rsi_analysis,
                "macd": macd_analysis
            }
        }
        
    except Exception as e:
        return {"status": "error", "message": str(e)}