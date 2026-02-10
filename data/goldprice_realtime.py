import yfinance as yf
import time

def get_realtime_gold():
    # 'GC=F' คือสัญลักษณ์ Gold Futures หรือ 'XAUUSD=X' สำหรับ Spot Gold
    gold = yf.Ticker("GC=F") 
    
    while True:
        data = gold.history(period="1d", interval="1m") # ดึงข้อมูลรายนาที
        if not data.empty:
            latest_price = data['Close'].iloc[-1]
            print(f"ราคาทองคำปัจจุบัน: ${latest_price:,.2f} USD")
        
        time.sleep(60) # อัปเดตทุก 60 วินาที

# เรียกใช้งาน
# get_realtime_gold()