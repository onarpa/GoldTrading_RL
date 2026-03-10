import os
from stable_baselines3 import PPO
from data_fetcher import fetch_historical_data
from indicators import add_technical_indicators
from trading_env import GoldTradingEnv

def train_ppo_model():
    # 1. ดึงข้อมูลและเตรียม State Space (ตัวแปร 15 ตัว)
    print("1. กำลังดึงข้อมูลและเตรียม State Space...")
    raw_df = fetch_historical_data(start_date="2005-01-01", end_date="2025-12-31")
    df_features = add_technical_indicators(raw_df)

    # 2. แบ่งข้อมูล Train (80%) และ Test (20%) 
    train_size = int(len(df_features) * 0.8)
    train_df = df_features.iloc[:train_size].reset_index(drop=True)
    test_df = df_features.iloc[train_size:].reset_index(drop=True)

    print(f"   -> ข้อมูลสำหรับฝึกสอน (Train): {len(train_df)} วัน")
    print(f"   -> ข้อมูลสำหรับทดสอบ (Test): {len(test_df)} วัน\n")

    # 3. สร้าง Environment จำลองตลาด
    print("2. สร้าง Environment จำลองตลาดสำหรับฝึกสอน...")
    env = GoldTradingEnv(df=train_df)

    # 4. เริ่มสร้างและฝึกสอนโมเดล PPO
    print("\n3. เริ่มสร้างและฝึกสอนโมเดล PPO (AI กำลังเรียนรู้)...")
    # MlpPolicy (Multi-Layer Perceptron) 
    model = PPO("MlpPolicy", env, verbose=1, learning_rate=0.0003)

    # สั่งให้ AI เดินทดลองเทรด 50,000 ก้าว (วัน)
    model.learn(total_timesteps=50000)

    # 5. Save Model
    print("\n4. กำลังบันทึกสมอง AI...")
    model_dir = os.path.join(os.path.dirname(__file__), "..", "models")
    os.makedirs(model_dir, exist_ok=True)
    
    model_path = os.path.join(model_dir, "ppo_gold_trading")
    model.save(model_path)
    print(f"   -> บันทึกโมเดลสำเร็จที่: {model_path}.zip\n")

    # 6. ทดสอบความฉลาดหลังเรียนจบ (บนข้อมูล Test ที่ AI ไม่เคยเห็นมาก่อน)
    print("5. ทดสอบการเทรดด้วยโมเดลที่ฝึกสอนแล้ว (บน Test Data 20 วันแรก)...")
    test_env = GoldTradingEnv(df=test_df)
    obs, _ = test_env.reset()

    for step in range(20):
        # ให้ AI ใช้สมอง (model.predict) ทายว่าควรกดปุ่มไหนจากข้อมูล obs ที่เห็น
        # deterministic=True คือบังคับให้มันเลือกทางเลือกที่ดีที่สุดที่มันคิดออก (เลิกสุ่ม)
        action, _states = model.predict(obs, deterministic=True)
        obs, reward, done, _, info = test_env.step(action)

        action_name = ["HOLD", "BUY", "SELL"][action]
        
        print(f"วันที่ {step+1:02d} | AI ตัดสินใจ: {action_name:<4} | กำไร/ขาดทุนรอบนี้: {reward:>6.2f} USD | พอร์ตสะสม: {info['net_worth']:.2f} USD")

if __name__ == "__main__":
    train_ppo_model()