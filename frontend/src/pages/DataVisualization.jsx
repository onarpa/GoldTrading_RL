import React, { useState, useEffect, useCallback } from 'react';
import Layout from '../components/Layout';
import CandleChart from '../components/CandleChart';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS, CategoryScale, LinearScale, PointElement,
  LineElement, Title, Tooltip, Legend, Filler
} from 'chart.js';
import { api, shiftLabels, toThai } from '../services/api';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler);


function ChartCard({ title, children, badge }) {
  return (
    <div className="bg-white p-5 rounded-xl shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold text-gray-700">{title}</h3>
        {badge && <span className="text-xs bg-indigo-50 text-indigo-600 px-2 py-0.5 rounded-full">{badge}</span>}
      </div>
      <div className="h-52">{children}</div>
    </div>
  );
}

const sharedTooltip = {
  backgroundColor: '#1e293b', titleColor: '#94a3b8',
  bodyColor: '#f1f5f9', borderColor: '#334155', borderWidth: 1, padding: 10,
};
const sharedScales = (yExtra = {}) => ({
  x: {
    grid: { color: 'rgba(0,0,0,0.03)', drawTicks: false },
    ticks: { maxTicksLimit: 8, color: '#9ca3af', font: { size: 10 } },
    border: { color: '#e5e7eb' },
  },
  y: {
    position: 'right',
    grid: { color: 'rgba(0,0,0,0.04)', drawTicks: false },
    ticks: { color: '#9ca3af', font: { size: 10 } },
    border: { color: '#e5e7eb' },
    ...yExtra,
  },
});
const opts = (yExtra = {}) => ({
  responsive: true, maintainAspectRatio: false,
  animation: { duration: 400 },
  interaction: { mode: 'index', intersect: false },
  plugins: {
    legend: { position: 'top', align: 'end',
      labels: { boxWidth: 20, boxHeight: 2, pointStyle: 'line', usePointStyle: true,
                font: { size: 10 }, color: '#6b7280', padding: 12 } },
    tooltip: sharedTooltip,
  },
  scales: sharedScales(yExtra),
});

/* RSI 30/70 reference lines */
const rsiRefPlugin = {
  id: 'rsiRef',
  afterDraw(chart) {
    const { ctx, chartArea: { left, right }, scales: { y } } = chart;
    [[70,'rgba(239,68,68,0.35)'],[30,'rgba(34,197,94,0.35)']].forEach(([val,color]) => {
      const yPos = y.getPixelForValue(val);
      ctx.save(); ctx.strokeStyle = color; ctx.lineWidth = 1; ctx.setLineDash([4,4]);
      ctx.beginPath(); ctx.moveTo(left,yPos); ctx.lineTo(right,yPos); ctx.stroke(); ctx.restore();
    });
  }
};

/* MACD zero line */
const zeroLinePlugin = {
  id: 'zeroLine',
  afterDraw(chart) {
    const { ctx, chartArea: { left, right }, scales: { y } } = chart;
    const yPos = y.getPixelForValue(0);
    ctx.save(); ctx.strokeStyle = 'rgba(100,116,139,0.35)'; ctx.lineWidth = 1; ctx.setLineDash([3,3]);
    ctx.beginPath(); ctx.moveTo(left,yPos); ctx.lineTo(right,yPos); ctx.stroke(); ctx.restore();
  }
};

export default function DataVisualization() {
  const [viz, setViz]         = useState(null);
  const [predictions, setPredictions] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try {
      const [v, t] = await Promise.all([
        api.getVisualization(),
        api.getTradesChart(100),
      ]);
      if (v.status === 'success') setViz(v);
      if (t.status === 'success') setPredictions(t.data || []);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { setLoading(true); load(); }, [load]);

  if (loading) return (
    <Layout>
      <div className="flex justify-center items-center h-64">
        <p className="text-gray-400 animate-pulse">กำลังโหลด...</p>
      </div>
    </Layout>
  );

  const labels = shiftLabels(viz?.labels || []);
  const noData = <div className="flex items-center justify-center h-full text-gray-300 text-sm">ยังไม่มีข้อมูล</div>;

  /* ── RSI ── */
  const rsiData = {
    labels,
    datasets: [{
      label: 'RSI (14)', data: viz?.rsi,
      borderColor: '#8b5cf6', borderWidth: 1.8,
      pointRadius: 0, tension: 0.3, fill: false,
    }]
  };

  /* ── MACD ── */
  const macdData = {
    labels,
    datasets: [
      { label:'MACD',   data: viz?.macd,        borderColor:'#3b82f6', borderWidth:1.8, pointRadius:0, tension:0.3 },
      { label:'Signal', data: viz?.macd_signal,  borderColor:'#ef4444', borderWidth:1.5, borderDash:[4,3], pointRadius:0, tension:0.3 },
    ]
  };

  /* ── Bollinger Bands — from backend ── */
  const hasBB = viz?.bb_upper?.some(Boolean);
  const bbData = hasBB ? {
    labels,
    datasets: [
      { label:'Price',    data: viz?.close, borderColor:'#3b82f6', borderWidth:2, pointRadius:0, tension:0.3,
        backgroundColor:(ctx)=>{
          const g=ctx.chart.ctx.createLinearGradient(0,0,0,ctx.chart.canvas.offsetHeight);
          g.addColorStop(0,'rgba(59,130,246,0.07)'); g.addColorStop(1,'rgba(59,130,246,0.00)');
          return g;
        }, fill:true },
      { label:'Upper BB', data: viz?.bb_upper, borderColor:'#f87171', borderWidth:1.2, borderDash:[5,4], pointRadius:0 },
      { label:'Mid BB',   data: viz?.bb_mid,   borderColor:'#9ca3af', borderWidth:1,   borderDash:[2,3], pointRadius:0 },
      { label:'Lower BB', data: viz?.bb_lower, borderColor:'#34d399', borderWidth:1.2, borderDash:[5,4], pointRadius:0 },
    ]
  } : null;

  /* indicator summary */
  const lastRsi   = viz?.rsi?.filter(Boolean).slice(-1)[0];
  const lastMacd  = viz?.macd?.filter(Boolean).slice(-1)[0];
  const lastSig   = viz?.macd_signal?.filter(Boolean).slice(-1)[0];
  const lastClose = viz?.close?.filter(Boolean).slice(-1)[0];
  const lastEma50 = viz?.ema_50?.filter(Boolean).slice(-1)[0];

  return (
    <Layout>
      <div className="container mx-auto px-4 pb-10">

        <div className="mb-5">
          <h2 className="text-lg font-bold text-gray-700">Data Visualization</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5 mb-6">

          {/* Candlestick + EMA (full width) */}
          <div className="md:col-span-2 bg-white p-5 rounded-xl shadow-sm">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold text-gray-700">ราคา XAU/USD (Candlestick) + EMA</h3>
              <div className="flex items-center gap-4 text-xs text-gray-400">
                <span className="flex items-center gap-1.5">
                  <span className="inline-block w-3 h-3 rounded-sm bg-teal-500"></span>Bullish
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="inline-block w-3 h-3 rounded-sm bg-red-400"></span>Bearish
                </span>
                <span className="text-indigo-500 font-medium">— EMA50</span>
                <span className="text-red-400 font-medium">- - EMA200</span>
              </div>
            </div>
            <div className="h-64">
              {labels.length > 0
                ? <CandleChart
                    labels={labels}
                    open={viz?.open||[]} high={viz?.high||[]}
                    low={viz?.low||[]}   close={viz?.close||[]}
                    ema50={viz?.ema_50||[]} ema200={viz?.ema_200||[]}
                    predictions={predictions}
                    height={256}
                  />
                : noData}
            </div>
          </div>

          {/* RSI */}
          <ChartCard title="RSI (14)" badge="Momentum">
            {labels.length > 0
              ? <Line data={rsiData} options={opts({min:0,max:100})} plugins={[rsiRefPlugin]} />
              : noData}
          </ChartCard>

          {/* MACD */}
          <ChartCard title="MACD (12, 26, 9)" badge="Trend">
            {labels.length > 0
              ? <Line data={macdData} options={opts()} plugins={[zeroLinePlugin]} />
              : noData}
          </ChartCard>

          {/* Bollinger Bands — candlestick with BB overlay (full width) */}
          <div className="md:col-span-2 bg-white p-5 rounded-xl shadow-sm">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold text-gray-700">Bollinger Bands (20, 2σ) + Candlestick</h3>
              <span className="text-xs bg-indigo-50 text-indigo-600 px-2 py-0.5 rounded-full">Volatility · คำนวณจาก Backend</span>
            </div>
            <div className="h-64">
              {labels.length > 0
                ? <CandleChart
                    labels={labels}
                    open={viz?.open||[]} high={viz?.high||[]}
                    low={viz?.low||[]}   close={viz?.close||[]}
                    bbUpper={viz?.bb_upper||[]}
                    bbMid={viz?.bb_mid||[]}
                    bbLower={viz?.bb_lower||[]}
                    height={256}
                  />
                : noData}
            </div>
          </div>

        </div>

        {/* Indicator Summary */}
        <div className="bg-white p-6 rounded-xl shadow-sm">
          <h3 className="font-semibold text-gray-800 mb-4">การวิเคราะห์ตัวชี้วัดทางเทคนิค (ล่าสุด)</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className={`p-4 rounded-lg ${lastClose>(lastEma50||0)?'bg-green-50':'bg-red-50'}`}>
              <p className="font-bold text-gray-700">Moving Average</p>
              <p className={`text-sm mt-1 ${lastClose>(lastEma50||0)?'text-green-600':'text-red-600'}`}>
                {lastClose>(lastEma50||0)?'ราคาเหนือ EMA50 ':'ราคาต่ำกว่า EMA50 '}
              </p>
              <p className="text-xs text-gray-500 mt-1">Close: {lastClose?.toFixed(2)} | EMA50: {lastEma50?.toFixed(2)}</p>
            </div>
            <div className={`p-4 rounded-lg ${!lastRsi?'bg-gray-50':lastRsi>70?'bg-red-50':lastRsi<30?'bg-green-50':'bg-yellow-50'}`}>
              <p className="font-bold text-gray-700">RSI</p>
              <p className={`text-sm mt-1 ${!lastRsi?'text-gray-400':lastRsi>70?'text-red-600':lastRsi<30?'text-green-600':'text-yellow-600'}`}>
                {!lastRsi?'N/A':lastRsi>70?`RSI ${lastRsi.toFixed(1)} — Overbought `:lastRsi<30?`RSI ${lastRsi.toFixed(1)} — Oversold `:`RSI ${lastRsi.toFixed(1)} — Neutral`}
              </p>
              <p className="text-xs text-gray-500 mt-1">{lastRsi>70?'อาจเกิด pullback':lastRsi<30?'โอกาส bounce':'อยู่ในเขตปกติ'}</p>
            </div>
            <div className={`p-4 rounded-lg ${(lastMacd||0)>(lastSig||0)?'bg-blue-50':'bg-orange-50'}`}>
              <p className="font-bold text-gray-700">MACD</p>
              <p className={`text-sm mt-1 ${(lastMacd||0)>(lastSig||0)?'text-blue-600':'text-orange-600'}`}>
                {(lastMacd||0)>(lastSig||0)?'MACD เหนือ Signal ':'MACD ต่ำกว่า Signal '}
              </p>
              <p className="text-xs text-gray-500 mt-1">MACD: {lastMacd?.toFixed(4)} | Signal: {lastSig?.toFixed(4)}</p>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}
