import yfinance as yf
import pandas as pd

def fetch_historical_data(start_date="2005-01-01", end_date="2025-12-31"):
    """
    ฟังก์ชันดึงข้อมูลราคาทองคำและราคาน้ำมันย้อนหลัง
    ตามขอบเขตงานวิจัยข้อ 1.3.1 และ 1.3.2
    """
    print(f"กำลังดึงข้อมูลตั้งแต่ {start_date} ถึง {end_date}...")
    
    # 1. ดึงข้อมูลทองคำ (Gold Futures อ้างอิงตลาดโลก)
    gold_data = yf.download("GC=F", start=start_date, end=end_date, threads=False)
    
    # 2. ดึงข้อมูลราคาน้ำมัน (Crude Oil WTI)
    oil_data = yf.download("CL=F", start=start_date, end=end_date, threads=False)
    
    # แก้ปัญหา yfinance เวอร์ชันใหม่ที่คืนค่าเป็นตารางซ้อนตาราง (MultiIndex)
    if isinstance(gold_data.columns, pd.MultiIndex):
        gold_data.columns = gold_data.columns.droplevel(1)
    if isinstance(oil_data.columns, pd.MultiIndex):
        oil_data.columns = oil_data.columns.droplevel(1)
    
    # เลือกเฉพาะคอลัมน์ที่ต้องการตามขอบเขตข้อ 1.3.1 (Open, High, Low, Close, Volume)
    gold_df = gold_data[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
    
    # นำราคาน้ำมันมาต่อเข้าด้วยกันตามขอบเขตข้อ 1.3.2
    gold_df['Oil_Price'] = oil_data['Close']
    
    # จัดการ Missing Values เนื่องจากวันหยุดทำการที่อาจไม่ตรงกัน
    gold_df.ffill(inplace=True) 
    gold_df.dropna(inplace=True) 
    
    print(f"ดึงข้อมูลและทำความสะอาดสำเร็จ! จำนวนข้อมูลพร้อมใช้งาน: {len(gold_df)} วัน")
    return gold_df

# บล็อกสำหรับทดสอบรันไฟล์นี้โดยตรง
if __name__ == "__main__":
    # ทดสอบดึงข้อมูลตามช่วงเวลาในงานวิจัย (2005 - 2025)
    df = fetch_historical_data(start_date="2005-01-01", end_date="2025-12-31")
    
    print("\nตัวอย่างข้อมูล 5 วันล่าสุด:")
    print(df.tail())