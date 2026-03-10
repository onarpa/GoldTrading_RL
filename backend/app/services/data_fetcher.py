import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import os

# ฟังก์ชันสำหรับโหลดข้อมูล Historical Data 20 ปี จากไฟล์ Kaggle
# ใช้สำหรับ 'ฝึกสอน (Train)' โมเดล AI เท่านั้น
def load_kaggle_training_data(csv_filename="xauusd_historical.csv"):
    try:
        # กำหนด path ไปหาไฟล์ CSV
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        csv_path = os.path.join(base_dir, "data", csv_filename)
        
        print(f"กำลังโหลดข้อมูลสำหรับ Train AI จากไฟล์: {csv_path}")
        df = pd.read_csv(csv_path)
        
        df.rename(columns={
            'time': 'Date', 'open': 'Open', 'high': 'High', 
            'low': 'Low', 'close': 'Close', 'volume': 'Volume'
        }, inplace=True, errors='ignore')
        
        # จัดการข้อมูลสูญหาย (Missing values)
        df.ffill(inplace=True)
        df.dropna(inplace=True)
        
        print(f"โหลดข้อมูล Kaggle สำเร็จ! จำนวน: {len(df)} แถว")
        return df
    
    except Exception as e:
        print(f"เกิดข้อผิดพลาดในการอ่านไฟล์ Kaggle: {e}")
        return pd.DataFrame()

# ฟังก์ชันสำหรับดึงข้อมูล Real-time รายชั่วโมง จาก yfinance
# ใช้สำหรับแสดงบน 'Dashboard' และส่งให้ AI ทำนาย (Predict) 
def fetch_live_hourly_data(days_back=5, interval="1h"):
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")

    print(f"กำลังดึงข้อมูล Live ตลาดโลก Timeframe {interval}...")
    
    # ดึงข้อมูลทองคำ (Gold Spot อ้างอิงจาก yfinance มักใช้ GC=F หรือ โบรคเกอร์ย่อย)
    gold_data = yf.download("GC=F", start=start_date, end=end_date, interval=interval, threads=False)

    if isinstance(gold_data.columns, pd.MultiIndex):
        gold_data.columns = gold_data.columns.droplevel(1)
        
    gold_df = gold_data[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
    gold_df.ffill(inplace=True) 
    gold_df.dropna(inplace=True) 
    
    # รีเซ็ต Index เพื่อให้เวลากลายเป็นคอลัมน์
    gold_df.reset_index(inplace=True)
    if 'Datetime' in gold_df.columns:
        gold_df.rename(columns={'Datetime': 'Date'}, inplace=True)
    
    return gold_df

if __name__ == "__main__":
    # ทดสอบดึงข้อมูล Live รายชั่วโมง
    live_df = fetch_live_hourly_data(days_back=2)
    print("\nข้อมูล Live 5 ชั่วโมงล่าสุด:")
    print(live_df.tail())

# โหลดข้อมูลราคาน้ำมันย้อนหลังจากไฟล์ Kaggle เพื่อใช้ประกอบการ Train โมเดล
def load_kaggle_oil_data(csv_filename="crude-oil-price.csv"):
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        csv_path = os.path.join(base_dir, "data", csv_filename)

        print(f"กำลังโหลดข้อมูลราคาน้ำมันจากไฟล์: {csv_path}")
        oil_df = pd.read_csv(csv_path)

        oil_df.rename(columns={
            'date': 'Date', 'price': 'Close', 'open': 'Open', 
            'high': 'High', 'low': 'Low', 'volume': 'Volume', 'percent_change': 'Change'
        }, inplace=True, errors='ignore')

        # แปลงคอลัมน์ Date เป็น datetime เพื่อให้ นำไป merge กับทองคำได้ง่าย
        if 'Date' in oil_df.columns:
            oil_df['Date'] = pd.to_datetime(oil_df['Date'], errors='coerce')

        oil_df.ffill(inplace=True)
        oil_df.dropna(inplace=True)

        print(f"โหลดข้อมูลน้ำมัน Kaggle สำเร็จ! จำนวน: {len(oil_df)} แถว")
        return oil_df

    except Exception as e:
        print(f"เกิดข้อผิดพลาดในการอ่านไฟล์น้ำมัน Kaggle: {e}")
        return pd.DataFrame()

# ดึงข้อมูลราคาน้ำมันดิบ WTI (CL=F) แบบ Real-time รายชั่วโมงจากตลาดโลก
# เพื่อใช้แสดงบน Dashboard และป้อนให้ AI ทำนายสถานการณ์ปัจจุบัน
def fetch_live_hourly_oil_data(days_back=5, interval="1h"):
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")

    print(f"กำลังดึงข้อมูลน้ำมันดิบ (WTI) Live Timeframe {interval}...")

    # ดึงข้อมูล Crude Oil WTI Futures (สัญลักษณ์ CL=F)
    oil_data = yf.download("CL=F", start=start_date, end=end_date, interval=interval, threads=False)

    # ป้องกันกรณีโหลดข้อมูลไม่สำเร็จ
    if oil_data.empty:
        print("ไม่สามารถดึงข้อมูลน้ำมันดิบรายชั่วโมงได้")
        return pd.DataFrame()
    
    # แก้ปัญหาตารางซ้อนของ yfinance
    if isinstance(oil_data.columns, pd.MultiIndex):
        oil_data.columns = oil_data.columns.droplevel(1)

    oil_df = oil_data[['Open', 'High', 'Low', 'Close', 'Volume']].copy()

    oil_df.rename(columns={'Close': 'Oil_Price'}, inplace=True)
    oil_df.ffill(inplace=True) 
    oil_df.dropna(inplace=True) 

    # จัดการ Index ของเวลา
    oil_df.reset_index(inplace=True)
    if 'Datetime' in oil_df.columns:
        oil_df.rename(columns={'Datetime': 'Date'}, inplace=True)

    return oil_df

if __name__ == "__main__":
    # ทดสอบดึงข้อมูล Live น้ำมันดิบ 2 วันย้อนหลัง
    live_oil_df = fetch_live_hourly_oil_data(days_back=2)
    if not live_oil_df.empty:
        print("\nข้อมูล Live น้ำมันดิบ (WTI) 5 ชั่วโมงล่าสุด:")
        print(live_oil_df.tail())