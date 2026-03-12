import gymnasium as gym
from gymnasium import spaces
from collections import deque
import numpy as np
import gc

def _compute_rsi(prices: np.ndarray, period: int = 14) -> np.ndarray:
    """Return RSI array (same length as prices; first `period` values are NaN)."""
    rsi = np.full(len(prices), np.nan, dtype=np.float32)
    if len(prices) < period + 1:
        return rsi
    deltas = np.diff(prices.astype(np.float64))
    gains  = np.where(deltas > 0, deltas, 0.0)
    losses = np.where(deltas < 0, -deltas, 0.0)

    avg_gain = np.mean(gains[:period])
    avg_loss = np.mean(losses[:period])

    for i in range(period, len(deltas)):
        avg_gain = (avg_gain * (period - 1) + gains[i])  / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        rs = avg_gain / avg_loss if avg_loss != 0 else np.inf
        rsi[i + 1] = 100.0 - 100.0 / (1.0 + rs)

    return rsi.astype(np.float32)

def _compute_ema(prices: np.ndarray, span: int) -> np.ndarray:
    """Exponential moving average."""
    alpha = 2.0 / (span + 1)
    ema = np.full(len(prices), np.nan, dtype=np.float64)
    # find first non-nan
    start = 0
    while start < len(prices) and np.isnan(prices[start]):
        start += 1
    if start >= len(prices):
        return ema.astype(np.float32)
    ema[start] = prices[start]
    for i in range(start + 1, len(prices)):
        if not np.isnan(prices[i]):
            ema[i] = alpha * prices[i] + (1.0 - alpha) * ema[i - 1]
        else:
            ema[i] = ema[i - 1]
    return ema.astype(np.float32)

def _compute_macd(
    prices: np.ndarray,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> tuple:
    """
    Returns (macd_line, signal_line, histogram) – each same length as prices.
    Values before sufficient history are NaN.
    """
    ema_fast   = _compute_ema(prices, fast)
    ema_slow   = _compute_ema(prices, slow)
    macd_line  = (ema_fast - ema_slow).astype(np.float32)
    sig_line   = _compute_ema(macd_line, signal).astype(np.float32)
    histogram  = (macd_line - sig_line).astype(np.float32)
    return macd_line, sig_line, histogram

def _compute_support_resistance(
    highs: np.ndarray,
    lows: np.ndarray,
    closes: np.ndarray,
    lookback: int = 20,
) -> tuple:
    """
    Rolling support (min low) and resistance (max high) over `lookback` bars.
    Returns (support, resistance) normalised as distance from close (ratio).
    """
    n = len(closes)
    support    = np.full(n, np.nan, dtype=np.float32)
    resistance = np.full(n, np.nan, dtype=np.float32)
    for i in range(lookback - 1, n):
        window_lo = lows[i - lookback + 1 : i + 1]
        window_hi = highs[i - lookback + 1 : i + 1]
        s = np.min(window_lo)
        r = np.max(window_hi)
        c = closes[i]
        if c > 0:
            support[i]    = (c - s) / c        # distance below current close (positive)
            resistance[i] = (r - c) / c        # distance above current close (positive)
        else:
            support[i]    = 0.0
            resistance[i] = 0.0
    return support, resistance


class TradingEnv(gym.Env):

    def __init__(
        self,
        df,
        oil_price_df=None,
        use_oil_price: bool = True,
        use_rsi: bool = True,
        use_macd: bool = True,
        use_support_resistance: bool = True,
        use_trend_regime: bool = True,        # ← ใหม่: EMA-based trend regime features
        rsi_period: int = 14,
        macd_fast: int = 12,
        macd_slow: int = 26,
        macd_signal: int = 9,
        sr_lookback: int = 20,
        trend_ema_fast: int = 50,             # ← EMA สั้น (trend regime)
        trend_ema_slow: int = 200,            # ← EMA ยาว (trend regime)
        trend_slope_window: int = 24,         # ← หน้าต่างคำนวณ slope (hours)
        initial_balance: float = 10_000.0,
        tp_bounds: tuple = (0.006, 0.015),
        sl_bounds: tuple = (0.003, 0.008),
        risk_bounds: tuple = (0.001, 0.01),  # max 1% risk per trade
        leverage: float = 100.0,
        max_open_orders: int = 1,
        stop_out_pct: float = 0.1,
        scaler=None,
        episode_logging: bool = True,
        logging_downsample: int = 1,
        gc_interval: int = 5000,
        reward_rolling_window: int = 10,
        reward_volatility_scale: float = 5.0,
        reward_drawdown_power: float = 1.5,
        min_rr: float = 1.3,
        spread_pct: float = 0.002,
        commission_per_lot: float = 0.0
    ):
        super().__init__()

        self.use_oil_price = bool(use_oil_price)
        if self.use_oil_price:
            if oil_price_df is None:
                raise ValueError(
                    "`use_oil_price=True` but `oil_price_df` was not provided.\n"
                    "Either pass `oil_price_df=<your_array>` or set `use_oil_price=False`."
                )
            if isinstance(oil_price_df, bool):
                raise TypeError(
                    "`oil_price_df` received a bool instead of an array.\n"
                    "Likely caused by passing arguments positionally — use keyword args:\n"
                    "  TradingEnv(df, oil_price_df=oil_df, use_oil_price=True)"
                )
            if not hasattr(oil_price_df, '__len__'):
                raise TypeError(f"`oil_price_df` must be array-like, got {type(oil_price_df)}")
        self.oil_price_df = oil_price_df

        self.use_rsi                = bool(use_rsi)
        self.use_macd               = bool(use_macd)
        self.use_support_resistance = bool(use_support_resistance)
        self.use_trend_regime       = bool(use_trend_regime)

        self.df       = df.reset_index(drop=True).copy()
        self.features = ['Open', 'High', 'Low', 'Close', 'Volume']
        self.raw_data = self.df[self.features].values.astype(np.float32)

        self.scaler = scaler
        if self.scaler is not None:
            try:
                scaled = self.scaler.fit_transform(self.df[self.features])
            except Exception:
                scaled = self.scaler.fit_transform(self.df[self.features].values)
            self.scaled_data = np.asarray(scaled, dtype=np.float32)
        else:
            self.scaled_data = (self.raw_data / 1000.0).astype(np.float32)

        if 'Date' in self.df.columns:
            self.dates = self.df['Date'].values
        else:
            self.dates = np.arange(len(self.df))

        close_prices = self.raw_data[:, 3]  # column index 3 = Close
        high_prices  = self.raw_data[:, 1]
        low_prices   = self.raw_data[:, 2]

        self._indicator_data = self._build_indicator_array(
            close_prices, high_prices, low_prices,
            rsi_period, macd_fast, macd_slow, macd_signal, sr_lookback,
            trend_ema_fast, trend_ema_slow, trend_slope_window,
        )  # shape: (N, n_indicator_features)

        self.initial_balance = float(initial_balance)
        self.balance         = float(initial_balance)
        self.equity          = float(initial_balance)
        self.leverage        = float(leverage)
        self.max_open_orders = int(max_open_orders)
        self.stop_out_pct    = float(stop_out_pct)

        self.tp_min, self.tp_max = tp_bounds
        self.sl_min, self.sl_max = sl_bounds
        self.risk_min, self.risk_max = risk_bounds

        self.current_step = 0
        self.done         = False

        self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(4,), dtype=np.float32)

        obs_dim = self._compute_obs_dim()
        self.observation_space = spaces.Box(
            low=np.full(obs_dim, -np.inf, dtype=np.float32),
            high=np.full(obs_dim, np.inf, dtype=np.float32),
            dtype=np.float32,
        )

        self.CONTRACT_SIZE        = 100.0
        self.MAX_LOTS_PER_ORDER   = 5.0
        self.MAX_TOTAL_LOTS       = self.MAX_LOTS_PER_ORDER * self.max_open_orders
        self.MAX_MARGIN_EXPOSURE  = 0.5

        self.orders        = []
        self.trades        = []
        self.order_history = []

        self.episode_logging     = bool(episode_logging)
        self.logging_downsample  = max(1, int(logging_downsample))
        self.gc_interval         = max(1, int(gc_interval))
        self._step_counter       = 0

        self.reward_rolling_window    = max(1, int(reward_rolling_window))
        self.reward_volatility_scale  = float(reward_volatility_scale)
        self.reward_drawdown_power    = float(reward_drawdown_power)
        self._equity_history          = deque(maxlen=max(2, self.reward_rolling_window))

        self.min_rr             = float(max(1.0, min_rr))
        self.spread_pct         = float(spread_pct)
        self.commission_per_lot = float(commission_per_lot)

        self._clear_episode_history()

    def _build_indicator_array(
        self, close, high, low,
        rsi_period, macd_fast, macd_slow, macd_signal, sr_lookback,
        trend_ema_fast=50, trend_ema_slow=200, trend_slope_window=24,
    ) -> np.ndarray:

        n = len(close)
        cols = []

        if self.use_rsi:
            rsi = _compute_rsi(close, rsi_period)
            rsi = rsi / 100.0  # normalise to [0, 1]
            cols.append(rsi)

        if self.use_macd:
            norm = np.where(close > 0, close, 1.0)  # avoid div-by-0
            macd_line, sig_line, histogram = _compute_macd(close, macd_fast, macd_slow, macd_signal)
            cols.append(macd_line  / norm)
            cols.append(sig_line   / norm)
            cols.append(histogram  / norm)

        if self.use_support_resistance:
            support, resistance = _compute_support_resistance(high, low, close, sr_lookback)
            cols.append(support)
            cols.append(resistance)

        if self.use_trend_regime:
            norm      = np.where(close > 0, close, 1.0)
            ema_fast  = _compute_ema(close, trend_ema_fast).astype(np.float64)
            ema_slow  = _compute_ema(close, trend_ema_slow).astype(np.float64)

            # 1. Price position relative to each EMA (signed ratio)
            price_vs_fast = ((close - ema_fast) / norm).astype(np.float32)
            price_vs_slow = ((close - ema_slow) / norm).astype(np.float32)

            # 2. EMA crossover signal: positive = EMA50 > EMA200 = golden cross = uptrend
            ema_cross = ((ema_fast - ema_slow) / norm).astype(np.float32)

            # 3. EMA slopes: rate of change over slope_window bars (normalised)
            sw = max(2, trend_slope_window)
            ema_fast_slope = np.full(n, np.nan, dtype=np.float32)
            ema_slow_slope = np.full(n, np.nan, dtype=np.float32)
            for i in range(sw, n):
                denom_f = abs(ema_fast[i - sw]) if abs(ema_fast[i - sw]) > 1e-8 else 1.0
                denom_s = abs(ema_slow[i - sw]) if abs(ema_slow[i - sw]) > 1e-8 else 1.0
                if not (np.isnan(ema_fast[i]) or np.isnan(ema_fast[i - sw])):
                    ema_fast_slope[i] = (ema_fast[i] - ema_fast[i - sw]) / denom_f
                if not (np.isnan(ema_slow[i]) or np.isnan(ema_slow[i - sw])):
                    ema_slow_slope[i] = (ema_slow[i] - ema_slow[i - sw]) / denom_s

            cols.extend([price_vs_fast, price_vs_slow, ema_cross,
                         ema_fast_slope, ema_slow_slope])

        if not cols:
            return np.empty((n, 0), dtype=np.float32)

        arr = np.column_stack(cols).astype(np.float32)   # (N, K)

        # forward-fill NaN → then fill remaining NaN with 0
        for col in range(arr.shape[1]):
            last_valid = 0.0
            for row in range(arr.shape[0]):
                if np.isnan(arr[row, col]):
                    arr[row, col] = last_valid
                else:
                    last_valid = arr[row, col]

        np.nan_to_num(arr, copy=False, nan=0.0, posinf=0.0, neginf=0.0)
        return arr

    def _compute_obs_dim(self) -> int:
        """Total observation dimension."""
        dim = self.scaled_data.shape[1]           # OHLCV scaled
        dim += self._indicator_data.shape[1]       # technical indicators
        if self.use_oil_price:
            oil_cols = (
                np.asarray(self.oil_price_df).shape[1]
                if hasattr(self.oil_price_df, 'shape') and len(np.asarray(self.oil_price_df).shape) > 1
                else 1
            )
            dim += oil_cols
        dim += 3                                   # balance_scaled, equity_scaled, open_orders_ratio
        return dim

    def _clear_episode_history(self):
        self._buy_count       = 0
        self._sell_count      = 0
        self.episode_rewards  = []
        self.episode_balances = []
        self.episode_equities = []
        self._episode_step    = 0
        self._equity_history.clear()

    def reset(self, seed=None, options=None):
        # support Gymnasium ≥ 0.26 API (seed / options) used by SB3
        super().reset(seed=seed)

        self.balance       = float(self.initial_balance)
        self.equity        = float(self.initial_balance)
        self.orders        = []
        self.trades        = []
        self.order_history = []
        self.current_step  = 0
        self.done          = False
        self._clear_episode_history()
        self._step_counter = 0
        self._equity_history.append(self.equity)

        obs = self._get_observation()
        info = {}
        return obs, info

    def _get_observation(self):
        parts = [self.scaled_data[self.current_step]]

        # technical indicators (pre-computed)
        if self._indicator_data.shape[1] > 0:
            parts.append(self._indicator_data[self.current_step])

        # oil price (optional)
        if self.use_oil_price:
            oil_val = np.asarray(self.oil_price_df[self.current_step], dtype=np.float32)
            if oil_val.ndim == 0:
                oil_val = oil_val.reshape(1)
            parts.append(oil_val)

        # account state
        balance_scaled      = self.balance / self.initial_balance
        equity_scaled       = self.equity  / self.initial_balance
        open_orders_ratio   = len(self.orders) / max(1, self.max_open_orders)
        parts.append(np.array([balance_scaled, equity_scaled, open_orders_ratio], dtype=np.float32))

        return np.concatenate(parts).astype(np.float32)

    def step(self, action):
        if self.done:
            return self._get_observation(), 0.0, True, False, {}

        # map action
        direction_raw, tp_raw, sl_raw, risk_raw = action
        direction = float(np.tanh(direction_raw))
        tp_pct = float(np.clip(
            self.tp_min + (tp_raw + 1) / 2 * (self.tp_max - self.tp_min),
            self.tp_min, self.tp_max,
        ))
        sl_pct = float(np.clip(
            self.sl_min + (sl_raw + 1) / 2 * (self.sl_max - self.sl_min),
            self.sl_min, self.sl_max,
        ))
        risk = float(np.clip(
            self.risk_min + (risk_raw + 1) / 2 * (self.risk_max - self.risk_min),
            self.risk_min, self.risk_max,
        ))

        # open order if capacity
        if abs(direction) >= 0.1 and len(self.orders) < self.max_open_orders:
            self._open_order(direction_raw, tp_pct, sl_pct, risk)

        # raw prices for simulation
        raw_row = self.raw_data[self.current_step]
        price   = float(raw_row[3])
        high    = float(raw_row[1])
        low     = float(raw_row[2])

        closed_orders  = []

        for o in list(self.orders):
            if o['direction'] == 'BUY':
                unrealized = (price - o['entry']) * o['lots'] * self.CONTRACT_SIZE
                if high >= o['tp']:
                    closed_orders.append((o, o['tp'],
                                          (o['tp'] - o['entry']) * o['lots'] * self.CONTRACT_SIZE))
                elif low <= o['sl']:
                    closed_orders.append((o, o['sl'],
                                          (o['sl'] - o['entry']) * o['lots'] * self.CONTRACT_SIZE))
            else:  # SELL
                unrealized = (o['entry'] - price) * o['lots'] * self.CONTRACT_SIZE
                if low <= o['tp']:
                    closed_orders.append((o, o['tp'],
                                          (o['entry'] - o['tp']) * o['lots'] * self.CONTRACT_SIZE))
                elif high >= o['sl']:
                    closed_orders.append((o, o['sl'],
                                          (o['entry'] - o['sl']) * o['lots'] * self.CONTRACT_SIZE))

            o['unrealized'] = float(np.nan_to_num(unrealized, nan=0.0, posinf=0.0, neginf=0.0))

        trade_signal = 0.0  # bonus/penalty จาก realized trade (ใช้ใน reward ด้านล่าง)
        for o, exit_price, profit in closed_orders:
            commission_cost = o.get('commission', 0.0)
            net_profit      = float(profit) - commission_cost
            self.balance   += float(profit)
            o['exit']        = float(exit_price)
            o['profit']      = float(net_profit)      # net หลังหัก commission
            o['gross_profit']= float(profit)
            o['balance_after'] = float(self.balance)
            o['exit_time']   = self.dates[self.current_step]
            self.trades.append(o)
            trade_signal    += net_profit / float(self.initial_balance)
            try:
                self.orders.remove(o)
            except ValueError:
                pass

        self.equity = float(self.balance + sum(o['unrealized'] for o in self.orders))

        profit_reward = (self.equity - self.initial_balance) / self.initial_balance

        self._equity_history.append(self.equity)
        if len(self._equity_history) >= 2:
            window     = min(len(self._equity_history), self.reward_rolling_window)
            recent     = list(self._equity_history)[-window:]
            rolling_std = np.std(recent) / max(1.0, self.initial_balance)
        else:
            rolling_std = 0.0

        drawdown         = max(0.0, (self.initial_balance - self.equity) / self.initial_balance)
        drawdown_penalty = drawdown ** self.reward_drawdown_power

        reward  = profit_reward / (1.0 + rolling_std * self.reward_volatility_scale)
        reward -= 0.3 * drawdown_penalty
        reward += 0.5 * trade_signal   # bonus/penalty จาก trade ที่ปิดใน step นี้
        if not self.done:
            reward += 0.001

        # stop-out check
        if self.equity < self.initial_balance * self.stop_out_pct:
            reward  -= 1.0
            self.done = True
            print(f"STOP OUT TRIGGERED at step {self.current_step}, equity={self.equity:.2f}")

        # advance
        self.current_step += 1
        if self.current_step >= len(self.df) - 1:
            print(f"DONE at step {self.current_step}, equity={self.equity:.4f}")
            self.done = True


        reward = float(np.clip(np.tanh(reward), -1.0, 1.0))

        if self.episode_logging and (self._episode_step % self.logging_downsample == 0):
            self.episode_rewards.append(reward)
            self.episode_balances.append(self.balance)
            self.episode_equities.append(self.equity)
        self._episode_step += 1

        self._step_counter += 1
        if self._step_counter % self.gc_interval == 0:
            gc.collect()

        obs  = self._get_observation()
        info = {'balance': self.balance, 'equity': self.equity, 'open_orders': len(self.orders)}

        if self.done and self.episode_logging:
            info.update({
                'episode_rewards':  self.episode_rewards,
                'episode_balances': self.episode_balances,
                'episode_equities': self.episode_equities,
            })
            self._clear_episode_history()

        return obs, reward, self.done, False, info


    def _open_order(self, direction, tp_pct, sl_pct, risk):
        idx        = self.current_step
        row_real   = self.raw_data[idx]
        start_time = self.dates[idx]

        entry_price = float(row_real[3]) * float(np.random.normal(1.0, 0.0002))
        # spread: BUY ซื้อที่ ask, SELL ขายที่ bid
        _d = direction
        if _d > 0.1:
            entry_price *= (1.0 + self.spread_pct)
        elif _d < -0.1:
            entry_price *= (1.0 - self.spread_pct)
        sl_pct = max(sl_pct, 0.002)

        risk_amount = self.balance * risk
        lots = risk_amount / (entry_price * sl_pct * self.CONTRACT_SIZE)
        lots = float(np.clip(lots, 0.01, self.MAX_LOTS_PER_ORDER))
        lots = float(np.nan_to_num(lots, nan=0.01, posinf=0.01, neginf=0.01))

        otype = 'BUY' if direction > 0.1 else 'SELL' if direction < -0.1 else 'HOLD'

        if otype == 'HOLD':
            return False

        # enforce minimum R:R
        if tp_pct < sl_pct * self.min_rr:
            tp_pct = float(np.clip(sl_pct * self.min_rr, self.tp_min, self.tp_max * 1.5))

        tp_price = float(entry_price * (1.0 + tp_pct) if otype == 'BUY' else entry_price * (1.0 - tp_pct))
        sl_price = float(entry_price * (1.0 - sl_pct) if otype == 'BUY' else entry_price * (1.0 + sl_pct))

        commission = self.commission_per_lot * lots
        margin     = float(lots * self.CONTRACT_SIZE * entry_price / self.leverage)
        # margin check รวม commission ด้วย
        if (margin + commission) > self.MAX_MARGIN_EXPOSURE * self.balance:
            return False

        self.balance -= commission

        # นับหลัง margin ผ่าน
        if otype == 'BUY':
            self._buy_count  += 1
        else:
            self._sell_count += 1

        order = {
            'order_id':     len(self.order_history) + 1,
            'start_idx':    idx,
            'start_time':   start_time,
            'entry':        entry_price,
            'tp':           tp_price,
            'sl':           sl_price,
            'direction':    otype,
            'tp_pct':       tp_pct,
            'sl_pct':       sl_pct,
            'lots':         lots,
            'risk':         risk,
            'margin':       margin,
            'commission':   commission,   # round-trip cost ที่จ่ายตอน open
            'unrealized':   0.0,
            'exit':         None,
            'profit':       None,         # net profit (หลังหัก commission)
            'gross_profit': None,
            'balance_after': None,
            'exit_time':    None,
        }
        self.orders.append(order)
        self.order_history.append(order.copy())
        return True

    def finalize_episode(self):
        if not self.episode_logging:
            return None
        return {
            'episode_rewards':  np.array(self.episode_rewards,  dtype=np.float32),
            'episode_balances': np.array(self.episode_balances, dtype=np.float32),
            'episode_equities': np.array(self.episode_equities, dtype=np.float32),
        }

    def indicator_info(self) -> dict:
        """Return a summary of which indicators are active and observation dim."""
        return {
            'use_oil_price':          self.use_oil_price,
            'use_rsi':                self.use_rsi,
            'use_macd':               self.use_macd,
            'use_support_resistance': self.use_support_resistance,
            'use_trend_regime':       self.use_trend_regime,
            'n_indicator_features':   self._indicator_data.shape[1],
            'obs_dim':                self.observation_space.shape[0],
            'spread_pct':             self.spread_pct,
            'commission_per_lot':     self.commission_per_lot,
        }