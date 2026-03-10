import random
import pandas as pd
import numpy as np

class GoldTradingEnv:
    # สภาพแวดล้อมจำลองสำหรับการเทรดทองคำ (Custom Environment สำหรับ RL)
    def __init__(self, df, initial_balance=10000.0, lot_size=1.0, margin_per_lot=100.0):
        self.df = df
        self.initial_balance = initial_balance
        self.lot_size = lot_size
        self.margin_per_lot = margin_per_lot
        self.reset()

    # รีเซ็ตสภาพแวดล้อมเมื่อเริ่มต้น Episode ใหม่
    def reset(self):
        self.current_step = 0
        self.balance = self.initial_balance
        self.orders = [] # เก็บสถานะที่เปิดอยู่ [{'type': 'buy'/'sell', 'price': float}]
        self.prev_unrealized = 0.0 # เก็บค่า Unrealized PnL ของตาก่อนหน้าเพื่อหา Smooth Gradient
        return self._get_state()

    # ส่งคืนข้อมูล Features ณ ปัจจุบันให้ AI
    def _get_state(self):
        return self.df.iloc[self.current_step]

    # รับ Action จาก AI และคำนวณผลลัพธ์พร้อม Reward
    # Action Space: 0 = Hold, 1 = Buy, 2 = Sell
    def step(self, action):
        current_price = self.df.iloc[self.current_step]['Close']
        reward_closed = 0.0
        
        # ระบบจัดการคำสั่งซื้อขาย (Order Execution)
        if action == 1: # Buy (ซื้อ / เปิด Long หรือ ปิด Short)
            shorts = [o for o in self.orders if o['type'] == 'sell']
            if shorts: # ถ้ามีออเดอร์ Sell ค้างอยู่ ให้ปิดสถานะ (Close)
                order_to_close = shorts[0]
                pnl = (order_to_close['price'] - current_price) * self.lot_size
                reward_closed += pnl
                self.balance += pnl
                self.orders.remove(order_to_close)
            else: # ถ้าไม่มี ให้เปิดออเดอร์ Buy ใหม่
                self.orders.append({'type': 'buy', 'price': current_price})
                
        elif action == 2: # Sell (ขาย / เปิด Short หรือ ปิด Long)
            buys = [o for o in self.orders if o['type'] == 'buy']
            if buys: # ถ้ามีออเดอร์ Buy ค้างอยู่ ให้ปิดสถานะ (Close)
                order_to_close = buys[0]
                pnl = (current_price - order_to_close['price']) * self.lot_size
                reward_closed += pnl
                self.balance += pnl
                self.orders.remove(order_to_close)
            else: # ถ้าไม่มี ให้เปิดออเดอร์ Sell ใหม่
                self.orders.append({'type': 'sell', 'price': current_price})
                
        # Action == 0 (Hold) จะไม่เกิดการเปิด/ปิดออเดอร์ใดๆ

        # การคำนวณฟังก์ชันรางวัล (Reward Function)
        # 1. Reward จาก Closed Orders (กำไร/ขาดทุนที่เกิดขึ้นจริงในตานี้) (ถูกคำนวณไว้ในตัวแปร reward_closed เรียบร้อยแล้ว)
        # 2. Reward จาก Order ที่ยังไม่ปิด (Unrealized - Smooth Gradient)
        current_unrealized = 0.0
        for order in self.orders:
            if order['type'] == 'buy':
                current_unrealized += (current_price - order['price']) * self.lot_size
            elif order['type'] == 'sell':
                current_unrealized += (order['price'] - current_price) * self.lot_size
                
        # รางวัลส่วนนี้คือ "ส่วนต่าง (Delta)" ของกำไรทิพย์จากตาก่อนหน้ามาตานี้
        reward_unrealized = current_unrealized - self.prev_unrealized
        self.prev_unrealized = current_unrealized
        
        # 3. Reward จาก Margin Usage (ป้องกัน Over-trading)
        # ยิ่งเปิดออเดอร์ค้างไว้เยอะ จะโดนหักคะแนนเล็กน้อยเป็นค่าเสียโอกาสหรือความเสี่ยง
        margin_used = len(self.orders) * self.margin_per_lot
        margin_penalty = margin_used * 0.005 # หักคะแนน 0.5% ของมาร์จิ้นที่ใช้ไปในแต่ละตา
        
        # ผลรวม Reward ที่จะส่งให้ AI ไปเรียนรู้
        total_reward = reward_closed + reward_unrealized - margin_penalty
        
        # ไปยังก้าวถัดไป
        self.current_step += 1
        done = self.current_step >= len(self.df) - 1 # จบ Episode เมื่อหมดแถวข้อมูล
        
        info = {
            'price': current_price,
            'action': action,
            'reward_closed': reward_closed,
            'reward_unrealized': reward_unrealized,
            'margin_penalty': margin_penalty,
            'total_reward': total_reward,
            'open_orders': len(self.orders),
            'equity': self.balance + current_unrealized
        }
        
        return self._get_state(), total_reward, done, info

# ทดสอบ: ให้ AI แบบสุ่ม (Random Agent) ลองเทรด 10 วันแรก
if __name__ == "__main__":
    # 1. จำลองข้อมูลราคาทองคำ 12 วัน (เพื่อให้เดินได้ 10 ก้าว)
    # ในการใช้งานจริง ให้รับ Dataframe จาก add_technical_indicators() มาใส่แทน
    mock_data = {
        'Close': [2000, 2010, 2005, 1990, 1980, 2020, 2030, 2025, 2040, 2050, 2045, 2060],
        'MACD': [1.2, 1.5, 1.1, -0.5, -1.2, 0.5, 1.8, 1.6, 2.5, 3.1, 2.8, 3.5]
    }
    df_mock = pd.DataFrame(mock_data)

    # 2. สร้าง Environment
    env = GoldTradingEnv(df_mock, initial_balance=10000)
    state = env.reset()

    print("เริ่มการทดสอบ Random AI Trading (10 ก้าวแรก)...\n")
    print(f"{'Step':<5} | {'Price':<6} | {'Action':<6} | {'Closed Rew':<10} | {'Unrealized Rew':<14} | {'Margin Pen':<10} | {'Total Rew':<10} | {'Orders':<6} | {'Equity'}")
    print("-" * 105)

    # 3. ให้ AI สุ่ม Action 10 ครั้ง
    actions_map = {0: 'HOLD', 1: 'BUY', 2: 'SELL'}
    
    for step in range(1, 11):
        # สุ่ม Action 0, 1 หรือ 2
        random_action = random.choice([0, 1, 2])
        # ส่ง Action เข้าไปใน Environment
        next_state, reward, done, info = env.step(random_action)
        # แสดงผลลัพธ์ในแต่ละก้าว
        act_str = actions_map[info['action']]
        print(f"{step:<5} | {info['price']:<6.1f} | {act_str:<6} | {info['reward_closed']:<10.2f} | {info['reward_unrealized']:<14.2f} | {-info['margin_penalty']:<10.2f} | {info['total_reward']:<10.2f} | {info['open_orders']:<6} | {info['equity']:.2f}")

    print("-" * 105)
    print("\nทดสอบเสร็จสิ้น")