import React, { useState, useEffect, useCallback } from 'react';
import Layout from '../components/Layout';
import { api, toThai, toThaiLong } from '../services/api';

function ActionBadge({ action, size = 'md' }) {
  const cfg = {
    BUY:  { bg: 'bg-green-100 text-green-700 border-green-300', dot: 'bg-green-500' },
    SELL: { bg: 'bg-red-100 text-red-700 border-red-300',   dot: 'bg-red-500'   },
    HOLD: { bg: 'bg-yellow-100 text-yellow-700 border-yellow-300', dot: 'bg-yellow-500' },
  };
  const c = cfg[action] || { bg: 'bg-gray-100 text-gray-500 border-gray-200', dot: 'bg-gray-400' };
  const sz = size === 'lg' ? 'text-2xl px-6 py-2' : 'text-xs px-3 py-1';
  return (
    <span className={`inline-flex items-center gap-2 rounded-full border font-bold ${sz} ${c.bg}`}>
      <span className={`w-2 h-2 rounded-full ${c.dot}`} />
      {action}
    </span>
  );
}

function ConfidenceBar({ value }) {
  const pct = Math.round(value * 100);
  const color = pct >= 70 ? 'bg-green-500' : pct >= 40 ? 'bg-yellow-400' : 'bg-red-400';
  return (
    <div className="w-full">
      <div className="flex justify-between text-xs text-gray-500 mb-1">
        <span>Confidence</span><span>{pct}%</span>
      </div>
      <div className="h-2 bg-gray-100 rounded-full">
        <div className={`h-2 rounded-full transition-all ${color}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

export default function PredictionResult() {
  const [latest, setLatest] = useState(null);
  const [history, setHistory] = useState([]);
  const [trades, setTrades] = useState(null);
  const [loading, setLoading] = useState(true);
  const [predicting, setPredicting] = useState(false);

  const load = useCallback(async () => {
    try {
      const [l, h, t] = await Promise.all([
        api.getLatestPrediction(),
        api.getPredictionHistory(20),
        api.getTrades(50),
      ]);
      if (l.status === 'success') setLatest(l.prediction);
      if (h.status === 'success') setHistory(h.data);
      if (t.status === 'success') setTrades(t);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); const i = setInterval(load, 300_000); return () => clearInterval(i); }, [load]);

  const handlePredict = async () => {
    setPredicting(true);
    try { await api.triggerPredict(); await load(); }
    finally { setPredicting(false); }
  };

  if (loading) return <Layout><div className="flex justify-center items-center h-64"><p className="text-gray-400 animate-pulse">กำลังโหลด...</p></div></Layout>;

  const summary = trades?.summary;

  return (
    <Layout>
      <div className="container mx-auto px-4 pb-10">

        {/* Trigger Button */}
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-lg font-bold text-gray-700">Prediction Result</h2>
          <button onClick={handlePredict} disabled={predicting}
            className="bg-indigo-600 hover:bg-indigo-700 text-white text-sm px-5 py-2 rounded-lg font-medium transition disabled:opacity-50">
            {predicting ? 'กำลัง Predict...' : 'Predict Now'}
          </button>
        </div>

        {/* Latest Prediction Card */}
        {latest ? (
          <div className="bg-white rounded-xl shadow-sm p-6 mb-6 border-l-4 border-indigo-500">
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
              <div>
                <p className="text-xs text-gray-400 mb-1">ผล Predict ล่าสุด — {toThaiLong(latest.timestamp)}</p>
                <ActionBadge action={latest.action} size="lg" />
                <p className="text-2xl font-bold text-gray-800 mt-2">
                  {latest.gold_price?.toLocaleString('en-US', { minimumFractionDigits: 2 })} <span className="text-sm text-gray-400">USD/oz</span>
                </p>
              </div>
              <div className="grid grid-cols-3 gap-4 text-center">
                {[
                  { label: 'Take Profit', val: latest.tp_price ? latest.tp_price.toLocaleString('en-US', {minimumFractionDigits:2}) : `+${latest.tp_pct?.toFixed(3)}%`, color: 'text-green-600' },
                  { label: 'Stop Loss',   val: latest.sl_price ? latest.sl_price.toLocaleString('en-US', {minimumFractionDigits:2}) : `-${latest.sl_pct?.toFixed(3)}%`, color: 'text-red-500'   },
                  { label: 'Model',       val: latest.model_version,             color: 'text-indigo-600'},
                ].map((x, i) => (
                  <div key={i} className="bg-gray-50 rounded-lg p-3">
                    <p className="text-xs text-gray-400">{x.label}</p>
                    <p className={`font-bold text-sm mt-1 ${x.color}`}>{x.val}</p>
                  </div>
                ))}
              </div>
            </div>
            <div className="mt-4">
              <ConfidenceBar value={latest.confidence} />
            </div>
          </div>
        ) : (
          <div className="bg-white rounded-xl p-6 mb-6 text-center text-gray-400">ยังไม่มีข้อมูล Prediction — กด "Predict Now"</div>
        )}

        {/* Trade Summary */}
        {summary && (
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
            {[
              { label: 'Total Trades', val: summary.total_trades, color: 'text-gray-800' },
              { label: 'Open',         val: summary.open_trades,  color: 'text-blue-600'  },
              { label: 'Win',          val: summary.win_trades,   color: 'text-green-600' },
              { label: 'Loss',         val: summary.loss_trades,  color: 'text-red-500'   },
              { label: 'Win Rate',     val: `${summary.win_rate}%`, color: summary.win_rate >= 50 ? 'text-green-600' : 'text-red-500' },
            ].map((x, i) => (
              <div key={i} className="bg-white p-4 rounded-lg shadow-sm text-center">
                <p className="text-xs text-gray-400">{x.label}</p>
                <p className={`text-2xl font-bold mt-1 ${x.color}`}>{x.val}</p>
              </div>
            ))}
          </div>
        )}

        {/* Prediction History Table */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <h3 className="text-lg font-semibold mb-4 text-gray-800">ประวัติ Prediction</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="text-xs text-gray-400 uppercase border-b">
                <tr>
                  {['เวลา', 'ราคา (USD)', 'Action', 'Confidence', 'TP Price', 'SL Price', 'Model'].map(h => (
                    <th key={h} className="py-3 pr-4">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="text-gray-600">
                {history.length === 0 ? (
                  <tr><td colSpan={7} className="py-8 text-center text-gray-300">ยังไม่มีข้อมูล</td></tr>
                ) : history.map((p, i) => (
                  <tr key={i} className="border-b hover:bg-gray-50 transition">
                    <td className="py-3 pr-4 text-xs">{toThaiLong(p.timestamp)}</td>
                    <td className="py-3 pr-4 font-medium">{p.gold_price?.toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
                    <td className="py-3 pr-4"><ActionBadge action={p.action} /></td>
                    <td className="py-3 pr-4">
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-1.5 bg-gray-100 rounded-full">
                          <div className={`h-1.5 rounded-full ${p.confidence >= 0.7 ? 'bg-green-500' : p.confidence >= 0.4 ? 'bg-yellow-400' : 'bg-red-400'}`}
                            style={{ width: `${p.confidence * 100}%` }} />
                        </div>
                        <span className="text-xs">{(p.confidence * 100).toFixed(0)}%</span>
                      </div>
                    </td>
                    <td className="py-3 pr-4 text-green-600">{p.tp_price ? p.tp_price.toLocaleString('en-US',{minimumFractionDigits:2}) : `+${p.tp_pct?.toFixed(3)}%`}</td>
                    <td className="py-3 pr-4 text-red-500">{p.sl_price ? p.sl_price.toLocaleString('en-US',{minimumFractionDigits:2}) : `-${p.sl_pct?.toFixed(3)}%`}</td>
                    <td className="py-3 text-xs text-indigo-600">{p.model_version}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Open Trades */}
        {trades?.trades && (
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h3 className="text-lg font-semibold mb-4 text-gray-800">Trade Log</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead className="text-xs text-gray-400 uppercase border-b">
                  <tr>
                    {['เปิด', 'ปิด', 'Direction', 'Entry', 'Exit', 'TP', 'SL', 'Lots', 'P&L', 'Status'].map(h => (
                      <th key={h} className="py-3 pr-4">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="text-gray-600">
                  {trades.trades.slice(0, 20).map((t, i) => (
                    <tr key={i} className="border-b hover:bg-gray-50">
                      <td className="py-2 pr-4 text-xs">{toThaiLong(t.open_time)}</td>
                      <td className="py-2 pr-4 text-xs">{t.close_time ? toThaiLong(t.close_time) : '—'}</td>
                      <td className="py-2 pr-4"><ActionBadge action={t.direction} /></td>
                      <td className="py-2 pr-4">{t.entry_price?.toFixed(2)}</td>
                      <td className="py-2 pr-4">{t.exit_price?.toFixed(2) || '—'}</td>
                      <td className="py-2 pr-4 text-green-600">{t.tp_price?.toFixed(2)}</td>
                      <td className="py-2 pr-4 text-red-500">{t.sl_price?.toFixed(2)}</td>
                      <td className="py-2 pr-4">{t.lots}</td>
                      <td className={`py-2 pr-4 font-medium ${(t.profit || 0) >= 0 ? 'text-green-600' : 'text-red-500'}`}>
                        {t.profit !== null ? `${t.profit >= 0 ? '+' : ''}${t.profit?.toFixed(2)}` : '—'}
                      </td>
                      <td className="py-2">
                        <span className={`text-xs px-2 py-0.5 rounded-full font-medium
                          ${t.status === 'WIN' ? 'bg-green-100 text-green-700' :
                            t.status === 'LOSS' ? 'bg-red-100 text-red-700' :
                            'bg-blue-100 text-blue-700'}`}>
                          {t.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
}
