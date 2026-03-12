import React, { useState, useEffect, useCallback } from 'react';
import Layout from '../components/Layout';
import { Line, Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS, CategoryScale, LinearScale, PointElement,
  LineElement, BarElement, Title, Tooltip, Filler, Legend
} from 'chart.js';
import { api, toThaiLong } from '../services/api';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, BarElement, Title, Tooltip, Filler, Legend);

function KpiCard({ label, value, sub, color = 'text-gray-800' }) {
  return (
    <div className="bg-white p-5 rounded-lg shadow-sm">
      <p className="text-gray-400 text-xs uppercase tracking-wide">{label}</p>
      <h2 className={`text-3xl font-bold mt-1 ${color}`}>{value}</h2>
      {sub && <p className="text-xs text-gray-400 mt-1">{sub}</p>}
    </div>
  );
}

/* zero-line plugin for bar chart */
const zeroLinePlugin = {
  id: 'zeroLine',
  afterDraw(chart) {
    const { ctx, chartArea: { left, right }, scales: { y } } = chart;
    const yPos = y.getPixelForValue(0);
    ctx.save();
    ctx.strokeStyle = 'rgba(100,116,139,0.3)'; ctx.lineWidth = 1; ctx.setLineDash([3, 3]);
    ctx.beginPath(); ctx.moveTo(left, yPos); ctx.lineTo(right, yPos); ctx.stroke();
    ctx.restore();
  }
};

const sharedTooltip = {
  backgroundColor: '#1e293b', titleColor: '#94a3b8',
  bodyColor: '#f1f5f9', borderColor: '#334155', borderWidth: 1, padding: 10,
};

export default function ModelPerformance() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [training, setTraining] = useState(false);
  const [trainResult, setTrainResult] = useState(null);
  const [models, setModels] = useState([]);
  const [selecting, setSelecting] = useState(false);

  const load = useCallback(async () => {
    try {
      const [d, m] = await Promise.all([api.getPerformance(), api.listModels()]);
      if (d.status === 'success') setData(d);
      if (m.status === 'success') setModels(m.models || []);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  }, []);

  const handleSelectModel = async (filename) => {
    setSelecting(true);
    try {
      await api.selectModel(filename);
      await load();
    } finally { setSelecting(false); }
  };

  useEffect(() => { load(); const i = setInterval(load, 300_000); return () => clearInterval(i); }, [load]);

  const handleRetrain = async () => {
    setTraining(true); setTrainResult(null);
    try {
      const r = await api.triggerTraining();
      setTrainResult(r);
      await load();
    } finally { setTraining(false); }
  };

  if (loading) return (
    <Layout>
      <div className="flex justify-center items-center h-64">
        <p className="text-gray-400 animate-pulse">กำลังโหลด...</p>
      </div>
    </Layout>
  );

  const s = data?.summary || {};
  const monthly = data?.monthly || [];
  const logs = data?.training_logs || [];

  /* ── Cumulative chart — gradient green ── */
  const cumValues = monthly.reduce((acc, m, i) => {
    acc.push((acc[i - 1] || 0) + m.profit);
    return acc;
  }, []);

  const cumulativeData = {
    labels: monthly.map(m => m.month),
    datasets: [{
      label: 'Cumulative Profit (USD)',
      data: cumValues,
      borderColor: '#10b981',
      borderWidth: 2,
      backgroundColor: (ctx) => {
        const g = ctx.chart.ctx.createLinearGradient(0, 0, 0, ctx.chart.canvas.offsetHeight);
        g.addColorStop(0, 'rgba(16,185,129,0.15)');
        g.addColorStop(1, 'rgba(16,185,129,0.00)');
        return g;
      },
      fill: true, tension: 0.4,
      pointRadius: 0, pointHoverRadius: 4, pointHoverBackgroundColor: '#10b981',
    }]
  };

  /* ── Monthly bar — green/red per value ── */
  const monthlyChartData = {
    labels: monthly.map(m => m.month),
    datasets: [{
      label: 'Monthly Profit (USD)',
      data: monthly.map(m => m.profit),
      backgroundColor: monthly.map(m => m.profit >= 0 ? 'rgba(16,185,129,0.75)' : 'rgba(239,68,68,0.75)'),
      borderColor:     monthly.map(m => m.profit >= 0 ? '#059669' : '#dc2626'),
      borderWidth: 1,
      borderRadius: 5,
      borderSkipped: false,
    }]
  };

  const lineOpts = {
    responsive: true, maintainAspectRatio: false,
    animation: { duration: 600 },
    interaction: { mode: 'index', intersect: false },
    plugins: {
      legend: { display: false },
      tooltip: {
        ...sharedTooltip,
        callbacks: { label: ctx => ` ${ctx.dataset.label}: $${ctx.parsed.y?.toFixed(2)}` },
      },
    },
    scales: {
      x: {
        grid: { color: 'rgba(0,0,0,0.03)', drawTicks: false },
        ticks: { color: '#9ca3af', font: { size: 10 } },
        border: { color: '#e5e7eb' },
      },
      y: {
        position: 'right',
        grid: { color: 'rgba(0,0,0,0.04)', drawTicks: false },
        ticks: { color: '#9ca3af', font: { size: 10 }, callback: v => `$${v}` },
        border: { color: '#e5e7eb' },
      },
    },
  };

  const barOpts = {
    ...lineOpts,
    plugins: { ...lineOpts.plugins, legend: { display: false } },
    scales: {
      ...lineOpts.scales,
      y: {
        ...lineOpts.scales.y,
        ticks: {
          ...lineOpts.scales.y.ticks,
          callback: v => `${v >= 0 ? '+' : ''}$${v}`,
        },
      },
    },
  };

  const statusColor = {
    SUCCESS: 'text-green-600 bg-green-50',
    RUNNING: 'text-blue-600 bg-blue-50',
    FAILED:  'text-red-600 bg-red-50',
  };

  return (
    <Layout>
      <div className="container mx-auto px-4 pb-10">

        <div className="flex flex-wrap justify-between items-center gap-3 mb-6">
          <h2 className="text-lg font-bold text-gray-700">Model Performance</h2>
          <div className="flex items-center gap-3">
            {/* Model selector */}
            {models.length > 0 && (
              <div className="flex items-center gap-2">
                <span className="text-xs text-gray-400">Active model:</span>
                <select
                  disabled={selecting}
                  onChange={e => handleSelectModel(e.target.value)}
                  value={models.find(m => m.active)?.filename || ''}
                  className="text-sm border border-gray-200 rounded-lg px-3 py-1.5 bg-white text-gray-700 shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-300 disabled:opacity-50 max-w-xs truncate"
                >
                  {models.map(m => (
                    <option key={m.filename} value={m.filename}>
                      {m.filename} ({m.size_mb} MB)
                    </option>
                  ))}
                </select>
                {selecting && <span className="text-xs text-indigo-500 animate-pulse">กำลังโหลด...</span>}
              </div>
            )}
            <button onClick={handleRetrain} disabled={training}
              className="bg-purple-600 hover:bg-purple-700 text-white text-sm px-5 py-2 rounded-lg font-medium transition disabled:opacity-50">
              {training ? 'กำลัง Train...' : 'Retrain Model'}
            </button>
          </div>
        </div>

        {trainResult && (
          <div className={`mb-4 p-4 rounded-lg text-sm font-medium
            ${trainResult.status === 'success'  ? 'bg-green-50 text-green-700' :
              trainResult.status === 'skipped'  ? 'bg-yellow-50 text-yellow-700' :
                                                   'bg-red-50 text-red-700'}`}>
            {trainResult.status === 'success'  && ` Retrain สำเร็จ — Version: ${trainResult.version}, Reward: ${trainResult.eval_reward?.toFixed(2) ?? 'N/A'}`}
            {trainResult.status === 'skipped'  && ` ${trainResult.message}`}
            {trainResult.status === 'failed'   && ` Training ล้มเหลว: ${trainResult.error}`}
          </div>
        )}

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <KpiCard label="Win Rate"      value={`${s.win_rate ?? 0}%`}              sub={`${s.win_trades ?? 0}W / ${s.loss_trades ?? 0}L`} color={s.win_rate >= 50 ? 'text-green-500' : 'text-red-500'} />
          <KpiCard label="Total Profit"  value={`$${(s.total_profit ?? 0).toFixed(0)}`} sub="USD (simulated)"  color={s.total_profit >= 0 ? 'text-green-500' : 'text-red-500'} />
          <KpiCard label="Profit Factor" value={(s.profit_factor ?? 0).toFixed(2)}  sub="PF > 1.0 = profitable" color={s.profit_factor >= 1 ? 'text-blue-500' : 'text-red-500'} />
          <KpiCard label="Sharpe Ratio"  value={(s.sharpe_ratio ?? 0).toFixed(2)}   sub="ความเสี่ยงปรับแล้ว"    color={s.sharpe_ratio >= 1 ? 'text-purple-500' : 'text-gray-600'} />
          <KpiCard label="Max Drawdown"  value={`${(s.max_drawdown ?? 0).toFixed(1)}%`} sub="การสูญเสียสูงสุด"  color="text-red-500" />
          <KpiCard label="Total Trades"  value={s.total_trades ?? 0}                sub="ทุก trades"             color="text-gray-800" />
          <KpiCard label="Avg R:R"       value={(s.avg_rr ?? 0).toFixed(2)}         sub="Risk:Reward ratio"      color="text-blue-600" />
          <KpiCard label="Model"         value={s.model_version ?? 'N/A'}           sub={`Reward: ${(s.eval_reward ?? 0).toFixed(0)}`} color="text-indigo-600" />
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <div className="bg-white p-6 rounded-lg shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-gray-700">Cumulative Profit (USD)</h3>
              <div className="flex items-center gap-2">
                <span className="inline-block w-5 h-0.5 bg-emerald-500"></span>
                <span className="text-xs text-gray-400">สะสม</span>
              </div>
            </div>
            <div className="h-56">
              {monthly.length > 0
                ? <Line data={cumulativeData} options={lineOpts} />
                : <div className="flex items-center justify-center h-full text-gray-300 text-sm">ยังไม่มีข้อมูล</div>}
            </div>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-gray-700">Monthly Performance</h3>
              <div className="flex items-center gap-3 text-xs text-gray-400">
                <span className="flex items-center gap-1"><span className="inline-block w-3 h-3 rounded-sm bg-emerald-400"></span>กำไร</span>
                <span className="flex items-center gap-1"><span className="inline-block w-3 h-3 rounded-sm bg-red-400"></span>ขาดทุน</span>
              </div>
            </div>
            <div className="h-56">
              {monthly.length > 0
                ? <Bar data={monthlyChartData} options={barOpts} plugins={[zeroLinePlugin]} />
                : <div className="flex items-center justify-center h-full text-gray-300 text-sm">ยังไม่มีข้อมูล</div>}
            </div>
          </div>
        </div>

        {/* Monthly table */}
        {monthly.length > 0 && (
          <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
            <h3 className="text-lg font-semibold mb-4 text-gray-800">สถิติรายเดือน</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead className="text-xs text-gray-400 uppercase border-b">
                  <tr>{['เดือน', 'Trades', 'Win', 'Win Rate', 'Profit (USD)'].map(h => <th key={h} className="py-3 pr-6">{h}</th>)}</tr>
                </thead>
                <tbody className="text-gray-600">
                  {[...monthly].reverse().map((m, i) => (
                    <tr key={i} className="border-b hover:bg-gray-50">
                      <td className="py-3 pr-6 font-medium">{m.month}</td>
                      <td className="py-3 pr-6">{m.trades}</td>
                      <td className="py-3 pr-6">{m.wins}</td>
                      <td className={`py-3 pr-6 font-medium ${m.win_rate >= 50 ? 'text-green-600' : 'text-red-500'}`}>{m.win_rate}%</td>
                      <td className={`py-3 font-bold ${m.profit >= 0 ? 'text-green-600' : 'text-red-500'}`}>
                        {m.profit >= 0 ? '+' : ''}{m.profit.toFixed(2)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Training Logs */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h3 className="text-lg font-semibold mb-4 text-gray-800">Training Logs</h3>
          {logs.length === 0 ? (
            <p className="text-gray-400 text-sm">ยังไม่มี training log — กด "Retrain Model" เพื่อเริ่ม</p>
          ) : (
            <div className="space-y-3">
              {logs.map((l, i) => (
                <div key={i} className="flex flex-col md:flex-row md:items-center gap-2 p-4 bg-gray-50 rounded-lg">
                  <div className="flex-1">
                    <div className="flex items-center gap-3">
                      <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${statusColor[l.status] || 'bg-gray-100 text-gray-600'}`}>
                        {l.status}
                      </span>
                      <span className="font-semibold text-gray-700">{l.model_version}</span>
                    </div>
                    <p className="text-xs text-gray-400 mt-1">เริ่ม: {toThaiLong(l.started_at)}</p>
                    {l.finished_at && <p className="text-xs text-gray-400">เสร็จ: {toThaiLong(l.finished_at)}</p>}
                    {l.error && <p className="text-xs text-red-400 mt-1"> {l.error}</p>}
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium text-gray-700">{l.timesteps.toLocaleString()} steps</p>
                    <p className="text-xs text-green-600">Best Reward: {l.best_reward?.toFixed(2)}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
}
