import pandas as pd
import numpy as np

# ฟังก์ชันสำหรับคำนวณและเพิ่มตัวชี้วัดทางเทคนิค (Feature Engineering)
# เพื่อใช้เป็น State (สภาพแวดล้อม) ให้โมเดล RL เรียนรู้
def add_technical_indicators(df):
    data = df.copy()

    # ตรวจสอบว่ามีข้อมูลเพียงพอต่อการคำนวณหรือไม่ (อย่างน้อยต้องมากกว่า 50 แท่งเทียน สำหรับ EMA50)
    if len(data) < 50:
        print("คำเตือน: ข้อมูลน้อยเกินไปสำหรับการคำนวณ Indicator บางตัว")
        return data

    # 1. Trend & Reversal (MACD และ EMA)
    # Exponential Moving Average (EMA) ระยะสั้นและระยะกลาง
    data['EMA_20'] = data['Close'].ewm(span=20, adjust=False).mean()
    data['EMA_50'] = data['Close'].ewm(span=50, adjust=False).mean()

    # MACD (Moving Average Convergence Divergence)
    ema_12 = data['Close'].ewm(span=12, adjust=False).mean()
    ema_26 = data['Close'].ewm(span=26, adjust=False).mean()
    data['MACD'] = ema_12 - ema_26
    data['MACD_Signal'] = data['MACD'].ewm(span=9, adjust=False).mean()
    data['MACD_Diff'] = data['MACD'] - data['MACD_Signal'] # ส่วนที่เป็นกราฟแท่ง (Histogram)

    # 2. Momentum & Volatility (RSI และ Bollinger Bands)
    # RSI (Relative Strength Index) 14 แท่งเทียน
    delta = data['Close'].diff()
    gain = delta.clip(lower=0).ewm(alpha=1/14, min_periods=14, adjust=False).mean()
    loss = -delta.clip(upper=0).ewm(alpha=1/14, min_periods=14, adjust=False).mean()
    rs = gain / loss
    data['RSI'] = 100 - (100 / (1.0 + rs))

    # Bollinger Bands (BOLL) อิงจาก SMA 20 และค่าเบี่ยงเบนมาตรฐาน (SD) 2 เท่า
    data['BOLL_Mid'] = data['Close'].rolling(window=20).mean()
    std_20 = data['Close'].rolling(window=20).std()
    data['BOLL_Upper'] = data['BOLL_Mid'] + (std_20 * 2)
    data['BOLL_Lower'] = data['BOLL_Mid'] - (std_20 * 2)

    # 3. Volume & Trend (VOL และ MA)
    # Moving Average (SMA) แบบปกติ
    data['MA_20'] = data['Close'].rolling(window=20).mean()
    
    # MA ของปริมาณการซื้อขาย (Volume Moving Average) ดูแนวโน้มแรงซื้อขายสะสม
    data['VOL_MA_20'] = data['Volume'].rolling(window=20).mean()

    # 4. ล้างข้อมูลส่วนที่คำนวณไม่ได้ (NaN) ออก
    # ข้อมูลช่วง 50 แท่งเทียนแรกจะเป็น NaN เพราะใช้คำนวณค่าเฉลี่ยย้อนหลังไม่ได้ จึงต้องดรอปทิ้ง
    data.dropna(inplace=True)
    data.reset_index(drop=True, inplace=True)

    return data

if __name__ == "__main__":
    from data_fetcher import fetch_live_hourly_data
    print("กำลังดึงข้อมูลดิบเพื่อทดสอบ Indicator...")
    raw_df = fetch_live_hourly_data(days_back=10) # ดึงเผื่อไว้ 10 วันเพื่อให้พอคำนวณ EMA50
    if not raw_df.empty:
        processed_df = add_technical_indicators(raw_df)
        print("\nผลลัพธ์ข้อมูลหลังทำ Feature Engineering (5 แท่งเทียนล่าสุด):")
        cols_to_show = ['Close', 'MACD', 'RSI', 'BOLL_Upper', 'BOLL_Lower', 'EMA_20', 'VOL_MA_20']
        print(processed_df[cols_to_show].tail())