import gymnasium as gym
from gymnasium import spaces
import numpy as np
import pandas as pd

class GoldTradingEnv(gym.Env):
    def __init__(self, df):
        super(GoldTradingEnv, self).__init__()
        self.df = df
        self.reward_range = (-np.inf, np.inf)
        
        # Actions: 0 = Hold, 1 = Buy, 2 = Sell
        self.action_space = spaces.Discrete(3)
        
        # Observation: Price data + Technical Indicators (simplified example)
        # In practice, include MACD, RSI, etc., from your feature engineering
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(10,), dtype=np.float32)

        self.reset()

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.current_step = 0
        self.balance = 10000  # Initial Balance
        self.shares_held = 0
        self.net_worth = 10000
        return self._next_observation(), {}

    def _next_observation(self):
        # Extract features for the current time step
        return self.df.iloc[self.current_step].values.astype(np.float32)

    def step(self, action):
        current_price = self.df.iloc[self.current_step]['Close']
        self.current_step += 1
        
        # Logic for Buy/Sell/Hold
        if action == 1: # Buy
            self.shares_held += self.balance / current_price
            self.balance = 0
        elif action == 2: # Sell
            self.balance += self.shares_held * current_price
            self.shares_held = 0

        self.net_worth = self.balance + (self.shares_held * current_price)
        
        # Reward Function (3.1 - 3.3 in your requirements)
        reward = self.net_worth - 10000 # Simplified reward
        
        done = self.current_step >= len(self.df) - 1
        return self._next_observation(), reward, done, False, {}