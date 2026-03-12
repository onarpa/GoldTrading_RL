import React, { useState, useEffect, useCallback } from 'react';
import Layout from '../components/Layout';
import CandleChart from '../components/CandleChart';
import { api, shiftLabels } from '../services/api';

function ActionBadge({ action }) {
  const colors = {
    BUY:  'bg-green-100 text-green-700 border border-green-300',
    SELL: 'bg-red-100 text-red-700 border border-red-300',
    HOLD: 'bg-yellow-100 text-yellow-700 border border-yellow-300',
    'N/A':'bg-gray-100 text-gray-500',
  };
  return (
    <span className={`inline-block px-4 py-1 rounded-full font-bold text-lg ${colors[action] || colors['N/A']}`}>
      {action}
    </span>
  );
}

export default function Dashboard() {
  const [data, setData]           = useState(null);
  const [predictions, setPredictions] = useState([]);
  const [loading, setLoading]     = useState(true);
  const [fetching, setFetching]   = useState(false);
  const [lastRefresh, setLastRefresh] = useState(null);

  const load = useCallback(async () => {
    try {
      const [d, t] = await Promise.all([
        api.getDashboard(),
        api.getTradesChart(100),
      ]);
      setData(d);
      if (t.status === 'success') setPredictions(t.data || []);
      setLastRefresh(new Date());
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => {
      load();
      const interval = setInterval(load, 120_000); // 2 นาที
      return () => clearInterval(interval);
  }, [load]);

  const handleFetch = async () => {
    setFetching(true);
    try { await api.fetchPrices(); await load(); }
    finally { setFetching(false); }
  };

  if (loading) return (
    <Layout>
      <div className="flex justify-center items-center h-64">
        <p className="text-xl text-gray-400 animate-pulse">กำลังโหลดข้อมูล...</p>
      </div>
    </Layout>
  );
  if (!data) return (
    <Layout>
      <div className="flex justify-center items-center h-64">
        <p className="text-red-500 font-medium">ไม่สามารถเชื่อมต่อ Backend ได้ กรุณาตรวจสอบว่า API ทำงานอยู่</p>
      </div>
    </Layout>
  );

  const chart  = data.chart || {};
  const tech   = data.technical || {};
  const pred   = data.prediction;

  return (
    <Layout>
      <div className="container mx-auto px-4 pb-10">

        {/* Header */}
        <div className="flex justify-between items-center mb-4">
          <div className="bg-indigo-600 text-white rounded-lg shadow-sm inline-flex px-6 py-3 font-medium">
            ราคาทองคำตลาดโลก (XAU/USD)
          </div>
          <div className="flex items-center gap-3">
            {lastRefresh && (
              <span className="text-xs text-gray-400">
                อัพเดท: {lastRefresh.toLocaleTimeString('th-TH', { timeZone: 'Asia/Bangkok' })}
              </span>
            )}
            <button onClick={handleFetch} disabled={fetching}
              className="bg-amber-500 hover:bg-amber-600 text-white text-sm px-4 py-2 rounded-lg font-medium transition disabled:opacity-50">
              {fetching ? 'กำลังดึงข้อมูล...' : 'ดึงข้อมูลใหม่'}
            </button>
          </div>
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
          <div className="bg-white p-5 rounded-lg shadow-sm">
            <p className="text-gray-500 text-sm">ราคาปัจจุบัน (XAU/USD)</p>
            <h2 className="text-3xl font-bold text-gray-800">{(data.current_price || 0).toLocaleString()}</h2>
            <p className="text-xs text-gray-400">USD / Ounce</p>
          </div>
          <div className="bg-white p-5 rounded-lg shadow-sm">
            <p className="text-gray-500 text-sm">เปลี่ยนแปลง (ชั่วโมงล่าสุด)</p>
            <h2 className={`text-3xl font-bold ${(data.price_change||0)>=0?'text-green-500':'text-red-500'}`}>
              {(data.price_change||0)>=0?'+':''}{(data.price_change||0).toFixed(2)}
            </h2>
            <p className={`text-xs ${(data.percent_change||0)>=0?'text-green-500':'text-red-500'}`}>
              ({(data.percent_change||0)>=0?'+':''}{(data.percent_change||0).toFixed(2)}%)
            </p>
          </div>
          <div className="bg-white p-5 rounded-lg shadow-sm">
            <p className="text-gray-500 text-sm mb-2">Technical Indicators</p>
            <p className="text-sm font-semibold text-gray-700">
              RSI: <span className={tech.rsi>70?'text-red-500':tech.rsi<30?'text-green-500':'text-blue-500'}>
                {tech.rsi?tech.rsi.toFixed(1):'N/A'}
              </span>
            </p>
            <p className="text-sm font-semibold text-gray-700">
              MACD: <span className={(tech.macd||0)>0?'text-green-500':'text-red-500'}>
                {tech.macd?tech.macd.toFixed(2):'N/A'}
              </span>
            </p>

          </div>
          <div className="bg-white p-5 rounded-lg shadow-sm border-l-4 border-yellow-400">
            <p className="text-gray-500 text-sm">ราคาน้ำมันดิบ (WTI)</p>
            <h2 className="text-3xl font-bold text-yellow-600">{(data.oil_price||0).toFixed(2)}</h2>
            <p className="text-xs text-gray-400">USD / Barrel</p>
          </div>
          <div className="bg-white p-5 rounded-lg shadow-sm border-l-4 border-indigo-500">
            <p className="text-gray-500 text-sm mb-2">คำแนะนำจาก RL Model</p>
            {pred ? (
              <>
                <ActionBadge action={pred.action} />
                <p className="text-xs text-gray-400 mt-2">Confidence: {(pred.confidence*100).toFixed(1)}%</p>
                <p className="text-xs text-gray-400">TP: {pred.tp_price ? pred.tp_price.toLocaleString('en-US',{minimumFractionDigits:2}) : `+${pred.tp_pct?.toFixed(2)}%`} / SL: {pred.sl_price ? pred.sl_price.toLocaleString('en-US',{minimumFractionDigits:2}) : `-${pred.sl_pct?.toFixed(2)}%`}</p>
              </>
            ) : (
              <p className="text-sm text-gray-400">ยังไม่มี prediction</p>
            )}
          </div>
        </div>

        {/* Candlestick Chart */}
        <div className="bg-white p-6 rounded-lg shadow-sm mb-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-800">กราฟราคาทองคำพร้อม EMA</h3>
            <div className="flex items-center gap-4 text-xs text-gray-400">
              <span className="flex items-center gap-1.5">
                <span className="inline-block w-3 h-3 rounded-sm bg-teal-500"></span>Bullish
              </span>
              <span className="flex items-center gap-1.5">
                <span className="inline-block w-3 h-3 rounded-sm bg-red-400"></span>Bearish
              </span>
              <span className="flex items-center gap-1.5">
                <span className="inline-block w-5 h-0.5 bg-indigo-500"></span>EMA50
              </span>
              <span className="flex items-center gap-1.5">
                <span className="inline-block w-5 h-0.5 bg-red-400" style={{borderTop:'2px dashed #ef4444',background:'none'}}></span>EMA200
              </span>
            </div>
          </div>
          <CandleChart
            labels={shiftLabels(chart.labels || [])}
            open={chart.open || []}
            high={chart.high || []}
            low={chart.low || []}
            close={chart.close || []}
            ema50={chart.ema_50 || []}
            ema200={chart.ema_200 || []}
            predictions={predictions}
            height={288}
          />
        </div>

        {/* EMA Analysis */}
        <div className="bg-white p-6 rounded-lg shadow-sm">
          <h3 className="font-semibold mb-3 text-gray-800">Trend Regime Analysis</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[
              { label:'EMA 50',  value: tech.ema_50?.toFixed(2)||'N/A',
                trend: data.current_price>(tech.ema_50||0)?'▲ ราคาเหนือ EMA50':'▼ ราคาต่ำกว่า EMA50',
                up: data.current_price>(tech.ema_50||0) },
              { label:'EMA 200', value: tech.ema_200?.toFixed(2)||'N/A',
                trend: data.current_price>(tech.ema_200||0)?'▲ ราคาเหนือ EMA200':'▼ ราคาต่ำกว่า EMA200',
                up: data.current_price>(tech.ema_200||0) },
              { label:'Golden/Death Cross',
                value: (tech.ema_50||0)>(tech.ema_200||0)?'Golden Cross ':'Death Cross ',
                trend: (tech.ema_50||0)>(tech.ema_200||0)?'EMA50 > EMA200 = Uptrend':'EMA50 < EMA200 = Downtrend',
                up: (tech.ema_50||0)>(tech.ema_200||0) },
            ].map((item,i) => (
              <div key={i} className={`p-4 rounded-lg ${item.up?'bg-green-50':'bg-red-50'}`}>
                <p className="font-bold text-gray-700 text-sm">{item.label}</p>
                <p className="text-lg font-bold mt-1">{item.value}</p>
                <p className={`text-xs mt-1 ${item.up?'text-green-600':'text-red-600'}`}>{item.trend}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </Layout>
  );
}
