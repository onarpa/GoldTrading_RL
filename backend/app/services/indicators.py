import pandas as pd
import ta

def add_technical_indicators(df):
    """
    เพิ่มตัวชี้วัดทางเทคนิค (Technical Indicators) ตามขอบเขตงานวิจัยข้อ 1.3.3
    เพื่อสร้าง State Space ให้กับโมเดล Reinforcement Learning
    """
    df = df.copy()
    
    # 1. Trend Indicators (ตัวชี้วัดแนวโน้ม)
    # EMA (Exponential Moving Average) 20 วัน และ 50 วัน
    df['EMA_20'] = ta.trend.ema_indicator(close=df['Close'], window=20)
    df['EMA_50'] = ta.trend.ema_indicator(close=df['Close'], window=50)
    
    # MACD (Moving Average Convergence Divergence)
    macd = ta.trend.MACD(close=df['Close'], window_slow=26, window_fast=12, window_sign=9)
    df['MACD'] = macd.macd()
    df['MACD_Signal'] = macd.macd_signal()
    df['MACD_Diff'] = macd.macd_diff()
    
    # 2. Momentum Indicators (ตัวชี้วัดโมเมนตัม)
    # RSI (Relative Strength Index) 14 วัน
    df['RSI'] = ta.momentum.rsi(close=df['Close'], window=14)
    
    # 3. Volatility Indicators (ตัวชี้วัดความผันผวน)
    # Bollinger Bands 20 วัน
    bollinger = ta.volatility.BollingerBands(close=df['Close'], window=20, window_dev=2)
    df['BB_High'] = bollinger.bollinger_hband()
    df['BB_Low'] = bollinger.bollinger_lband()
    df['BB_Mid'] = bollinger.bollinger_mavg()
    
    # ลบแถวที่มีค่า NaN ทิ้ง (การคำนวณย้อนหลัง เช่น EMA 50 วัน จะทำให้ 50 วันแรกไม่มีค่า)
    df.dropna(inplace=True)
    
    return df

# บล็อกสำหรับทดสอบรันไฟล์นี้โดยตรง
if __name__ == "__main__":
    from data_fetcher import fetch_historical_data
    
    # ดึงข้อมูลดิบมาทดสอบ
    raw_df = fetch_historical_data(start_date="2005-01-01", end_date="2025-12-31")
    
    print("\nกำลังคำนวณ Technical Indicators...")
    df_with_indicators = add_technical_indicators(raw_df)
    
    print(f"คำนวณสำเร็จ! จำนวนข้อมูลพร้อมเทรน AI: {len(df_with_indicators)} วัน")
    print("\nคอลัมน์ทั้งหมดที่ AI จะมองเห็น (State Space):")
    print(df_with_indicators.columns.tolist())
    print("\nตัวอย่างข้อมูล 5 วันล่าสุด (เฉพาะบางคอลัมน์):")
    print(df_with_indicators[['Close', 'Oil_Price', 'RSI', 'MACD', 'EMA_20']].tail())