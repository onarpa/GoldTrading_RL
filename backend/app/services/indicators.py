import pandas as pd
import ta

def add_technical_indicators(df):
    """
    ฟังก์ชันสำหรับเพิ่มตัวชี้วัดทางเทคนิค (Technical Indicators) ตามขอบเขตงานวิจัยข้อ 1.3.3
    โดยใช้ไลบรารี 'ta' เพื่อหลีกเลี่ยงปัญหา Version Conflict ของ Numba
    """
    df = df.copy()
    
    # 1. Trend Indicators: EMA และ MACD
    df['EMA_20'] = ta.trend.ema_indicator(close=df['Close'], window=20)
    df['EMA_50'] = ta.trend.ema_indicator(close=df['Close'], window=50)
    
    macd = ta.trend.MACD(close=df['Close'], window_slow=26, window_fast=12, window_sign=9)
    df['MACD'] = macd.macd()
    df['MACD_Signal'] = macd.macd_signal()
    df['MACD_Diff'] = macd.macd_diff()
    
    # 2. Momentum Indicators: RSI และ Bollinger Bands
    df['RSI'] = ta.momentum.rsi(close=df['Close'], window=14)
    
    bollinger = ta.volatility.BollingerBands(close=df['Close'], window=20, window_dev=2)
    df['BB_High'] = bollinger.bollinger_hband()
    df['BB_Low'] = bollinger.bollinger_lband()
    df['BB_Mid'] = bollinger.bollinger_mavg()
    
    # 3. Volume-based Indicators
    df.dropna(inplace=True)
    return df

if __name__ == "__main__":
    from data_fetcher import fetch_historical_data
    
    print("กำลังดึงข้อมูลทดสอบ...")
    raw_df = fetch_historical_data(start_date="2023-01-01", end_date="2024-01-01")
    
    print("กำลังคำนวณ Technical Indicators...")
    df_with_indicators = add_technical_indicators(raw_df)
    
    print("\nคอลัมน์ทั้งหมดพร้อมใช้สำหรับ AI Environment:")
    print(df_with_indicators.columns.tolist())
    print("\nตัวอย่างข้อมูล 5 วันล่าสุด:")
    print(df_with_indicators.tail())