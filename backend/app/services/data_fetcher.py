import yfinance as yf
import pandas as pd

def fetch_historical_data(start_date="2005-01-01", end_date="2025-12-31"):
    print(f"กำลังดึงข้อมูลตั้งแต่ {start_date} ถึง {end_date}...")
    
    # 1. ดึงข้อมูลทองคำ (XAU/USD)
    gold_data = yf.download("GC=F", start=start_date, end=end_date)
    
    # 2. ดึงข้อมูลราคาน้ำมัน (Crude Oil WTI)
    oil_data = yf.download("CL=F", start=start_date, end=end_date)
    
    if isinstance(gold_data.columns, pd.MultiIndex):
        gold_data.columns = gold_data.columns.droplevel(1)
    if isinstance(oil_data.columns, pd.MultiIndex):
        oil_data.columns = oil_data.columns.droplevel(1)
        
    # ทำความสะอาดและเลือกเฉพาะคอลัมน์ที่ต้องการ (Open, High, Low, Close, Volume)
    gold_df = gold_data[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
    
    # นำราคาน้ำมันมาต่อเข้าด้วยกัน (ใช้ราคา Close ของน้ำมันเป็นตัวแปรเศรษฐกิจ)
    gold_df['Oil_Price'] = oil_data['Close']
    
    # เติมข้อมูลที่แหว่งไป (Missing Values) ด้วยข้อมูลของวันก่อนหน้า (Forward Fill)
    gold_df.ffill(inplace=True)
    
    # ลบแถวที่ยังมีค่า NaN เหลืออยู่
    gold_df.dropna(inplace=True)
    
    print("ดึงข้อมูลสำเร็จ! จำนวนข้อมูล:", len(gold_df), "วัน")
    return gold_df

# ทดสอบรันไฟล์นี้ตรงๆ
if __name__ == "__main__":
    df = fetch_historical_data(start_date="2020-01-01", end_date="2024-01-01")
    print(df.head())