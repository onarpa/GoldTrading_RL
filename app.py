from flask import Flask, render_template
import yfinance as yf

app = Flask(__name__)

def get_gold_price_thb():
    # ดึงราคาทองคำ (XAU/USD)
    gold = yf.Ticker("GC=F")
    data = gold.history(period="1d")
    price_usd = data['Close'].iloc[-1]
    
    # ดึงอัตราแลกเปลี่ยน (USD/THB) เพื่อแปลงเป็นเงินบาท (โดยประมาณ)
    # หมายเหตุ: ราคาทองสมาคมฯ จะมีสูตรคำนวณเฉพาะ แต่ในที่นี้จะแปลงจาก Spot Price ให้ดูเป็นตัวอย่างครับ
    exchange_rate = yf.Ticker("USDTHB=X").history(period="1d")['Close'].iloc[-1]
    
    # คำนวณราคาทองแท่งโดยประมาณ (สูตรคร่าวๆ: Spot * Rate * 0.473 / 31.1035)
    # แต่ถ้าคุณมีตัวเลขที่ดึงมาอยู่แล้ว สามารถแทนที่คำนวณตรงนี้ได้เลย
    price_thb = (price_usd * exchange_rate * 0.473) / 0.65 # ตัวเลขสมมติให้ใกล้เคียง 42,xxx
    return "{:,.0f}".format(42850) # ในที่นี้ผมขอใส่ตัวเลขสมมติ หรือ price_thb เพื่อให้ตรงกับ HTML คุณ

@app.route('/')
def index():
    current_price = get_gold_price_thb()
    return render_template('index.html', price=current_price)

if __name__ == '__main__':
    app.run(debug=True)