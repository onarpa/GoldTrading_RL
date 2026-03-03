import gymnasium as gym
from gymnasium import spaces
import numpy as np
import pandas as pd

class GoldTradingEnv(gym.Env):
    def __init__(self, df, initial_balance=10000):
        super(GoldTradingEnv, self).__init__()
        
        # รีเซ็ต Index เพื่อให้วนลูปง่ายขึ้น
        self.df = df.reset_index(drop=True)
        self.initial_balance = initial_balance
        
        # กำหนด Action Space (สิ่งที่ AI ทำได้)
        # 0 = Hold (อยู่เฉยๆ/ถือสถานะเดิม)
        # 1 = Buy (ซื้อ/เปิดสถานะ Long)
        # 2 = Sell (ขาย/ปิดสถานะ)
        self.action_space = spaces.Discrete(3)
        
        # ตัดคอลัมน์ที่ไม่ใช่ตัวเลขออก (เช่น Date) ถ้ามี
        self.feature_cols = [col for col in self.df.columns if col != 'Date']
        
        # กำหนด Observation Space (สิ่งที่ AI มองเห็น: ตัวเลข Indicator ทั้ง 15 ตัว)
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, 
            shape=(len(self.feature_cols),), 
            dtype=np.float32
        )

    def reset(self, seed=None, options=None):
        """ รีเซ็ตตลาดกลับไปสู่วันแรก เพื่อเริ่ม Episode ใหม่ """
        super().reset(seed=seed)
        self.current_step = 0
        self.balance = self.initial_balance
        self.net_worth = self.initial_balance
        self.is_holding = False # สถานะว่าตอนนี้ถือทองอยู่ไหม
        
        return self._next_observation(), {}

    def _next_observation(self):
        """ ส่งข้อมูลแถวปัจจุบัน (State) ไปให้ AI ดู """
        obs = self.df.loc[self.current_step, self.feature_cols].values
        return obs.astype(np.float32)

    def step(self, action):
        """ AI เลือก Action -> ตลาดเปลี่ยนวัน -> คำนวณกำไร/ขาดทุน """
        prev_price = self.df.loc[self.current_step, 'Close']
        self.current_step += 1
        
        # ตรวจสอบว่าถึงวันสุดท้ายของข้อมูลหรือยัง
        done = self.current_step >= len(self.df) - 1
        if done:
            return self._next_observation(), 0, done, False, {'net_worth': self.net_worth}
        
        current_price = self.df.loc[self.current_step, 'Close']
        
        # AI ลงมือทำ Action
        if action == 1: # Buy
            self.is_holding = True
        elif action == 2: # Sell
            self.is_holding = False
        # ถ้า action == 0 (Hold) จะคงสถานะ self.is_holding ไว้เหมือนเดิม
        
        # คำนวณ Reward (รางวัล)
        # ถ้าถือทองอยู่ จะได้กำไร/ขาดทุน จากส่วนต่างราคาของวันนี้กับเมื่อวาน
        reward = 0
        if self.is_holding:
            reward = current_price - prev_price
            
        # อัปเดตพอร์ตการลงทุน (สมมติว่าซื้อ 1 ออนซ์)
        if self.is_holding:
            self.net_worth += reward
            
        obs = self._next_observation()
        info = {'net_worth': self.net_worth}
        
        return obs, reward, done, False, info

# บล็อกทดสอบรัน Environment ด้วย AI แบบสุ่ม
if __name__ == "__main__":
    from data_fetcher import fetch_historical_data
    from indicators import add_technical_indicators
    
    # 1. เตรียมข้อมูล
    print("กำลังเตรียมข้อมูลให้สนามฝึกซ้อม...")
    raw_df = fetch_historical_data(start_date="2020-01-01", end_date="2023-12-31")
    df_features = add_technical_indicators(raw_df)
    
    # 2. สร้าง Environment
    env = GoldTradingEnv(df=df_features)
    obs, _ = env.reset()
    
    print(f"สร้าง Environment สำเร็จ! AI มองเห็นตัวแปร {len(obs)} ตัว")
    
    # 3. ลองให้ AI แบบโง่ๆ (สุ่ม Action) เดิน 10 วันดูผลลัพธ์
    print("\nทดสอบให้ AI แบบสุ่ม ลองเทรด 10 วันแรก:")
    for step in range(10):
        # สุ่มเลข 0, 1, 2
        random_action = env.action_space.sample() 
        obs, reward, done, _, info = env.step(random_action)
        
        action_name = ["HOLD", "BUY", "SELL"][random_action]
        print(f"วันที่ {step+1} | Action: {action_name:<4} | Reward: {reward:>6.2f} | Net Worth: {info['net_worth']:.2f}")