import React, { useState, useEffect } from 'react';
import Layout from '../components/Layout';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS, CategoryScale, LinearScale, PointElement,
  LineElement, Title, Tooltip, Legend
} from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

export default function DataVisualization() {
  const [vizData, setVizData] = useState(null);
  const [loading, setLoading] = useState(true);

  // ดึงข้อมูลจริงจาก Backend
  useEffect(() => {
    fetch('http://127.0.0.1:8000/api/data-visualization')
      .then(res => res.json())
      .then(data => {
        if (data.status === 'success') {
          setVizData(data);
        }
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  if (loading) return <Layout activePage="visualization"><div className="flex h-screen items-center justify-center">กำลังโหลดข้อมูล...</div></Layout>;
  if (!vizData) return <Layout activePage="visualization"><div className="flex h-screen items-center justify-center text-red-500">ไม่สามารถเชื่อมต่อฐานข้อมูลได้</div></Layout>;

  // การตั้งค่า Options กลางสำหรับทุกกราฟ
  const commonOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { position: 'top' } },
    scales: { x: { ticks: { maxTicksLimit: 8 } } } // ป้องกันวันที่ซ้อนกัน
  };

  const maData = {
    labels: vizData.labels,
    datasets: [
      { label: 'Price', data: vizData.price, borderColor: '#3b82f6', tension: 0.1 },
      { label: 'MA20', data: vizData.ma20, borderColor: '#f59e0b', tension: 0.4 }
    ]
  };

  const rsiData = {
    labels: vizData.labels,
    datasets: [{ label: 'RSI', data: vizData.rsi, borderColor: '#8b5cf6', tension: 0.1 }]
  };

  const macdData = {
    labels: vizData.labels,
    datasets: [
      { label: 'MACD', data: vizData.macd, borderColor: '#3b82f6' },
      { label: 'Signal', data: vizData.macd_signal, borderColor: '#ef4444' }
    ]
  };

  const bbData = {
    labels: vizData.labels,
    datasets: [
      { label: 'Price', data: vizData.price, borderColor: '#3b82f6' },
      { label: 'Upper', data: vizData.bb_upper, borderColor: '#f87171', borderDash: [5,5], pointRadius: 0 },
      { label: 'Lower', data: vizData.bb_lower, borderColor: '#34d399', borderDash: [5,5], pointRadius: 0 }
    ]
  };

  // ฟังก์ชันตัวช่วยสำหรับเปลี่ยนสีกล่องวิเคราะห์อัตโนมัติ
  const getThemeClass = (theme) => {
    const themes = {
      'green': { bg: 'bg-green-50', textMain: 'text-green-600', textSub: 'text-green-500' },
      'red': { bg: 'bg-red-50', textMain: 'text-red-600', textSub: 'text-red-500' },
      'yellow': { bg: 'bg-yellow-50', textMain: 'text-yellow-600', textSub: 'text-yellow-500' },
      'blue': { bg: 'bg-blue-50', textMain: 'text-blue-600', textSub: 'text-blue-500' }
    };
    return themes[theme] || { bg: 'bg-gray-50', textMain: 'text-gray-600', textSub: 'text-gray-500' };
  };

  const an_ma = vizData.analysis.ma;
  const an_rsi = vizData.analysis.rsi;
  const an_macd = vizData.analysis.macd;

  return (
    <Layout activePage="visualization">
      <div className="container mx-auto px-4 pb-10 mt-6">
        
        {/* Charts Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <div className="bg-white p-4 rounded-lg shadow-sm">
            <h3 className="font-semibold mb-2">Moving Averages (20 วัน)</h3>
            <div className="h-60"><Line data={maData} options={commonOptions} /></div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow-sm">
            <h3 className="font-semibold mb-2">RSI Indicator</h3>
            <div className="h-60"><Line data={rsiData} options={{...commonOptions, scales: { y: { min: 0, max: 100 } }}} /></div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow-sm">
            <h3 className="font-semibold mb-2">MACD</h3>
            <div className="h-60"><Line data={macdData} options={commonOptions} /></div>
          </div>
        </div>

        {/* Indicator Analysis */}
        <div className="bg-white p-6 rounded-lg shadow-sm">
          <h3 className="font-semibold mb-4 text-lg">การวิเคราะห์ตัวชี้วัดทางเทคนิค (Real-time)</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-center">
            
            <div className={`${getThemeClass(an_ma.theme).bg} p-4 rounded`}>
              <p className="font-bold text-gray-700">{an_ma.title}</p>
              <p className={`text-sm ${getThemeClass(an_ma.theme).textMain} mt-1`}>{an_ma.condition}</p>
              <p className={`text-xs ${getThemeClass(an_ma.theme).textSub}`}>{an_ma.signal}</p>
            </div>
            
            <div className={`${getThemeClass(an_rsi.theme).bg} p-4 rounded`}>
              <p className="font-bold text-gray-700">{an_rsi.title}</p>
              <p className={`text-sm ${getThemeClass(an_rsi.theme).textMain} mt-1`}>{an_rsi.condition}</p>
              <p className={`text-xs ${getThemeClass(an_rsi.theme).textSub}`}>{an_rsi.signal}</p>
            </div>
            
            <div className={`${getThemeClass(an_macd.theme).bg} p-4 rounded`}>
              <p className="font-bold text-gray-700">{an_macd.title}</p>
              <p className={`text-sm ${getThemeClass(an_macd.theme).textMain} mt-1`}>{an_macd.condition}</p>
              <p className={`text-xs ${getThemeClass(an_macd.theme).textSub}`}>{an_macd.signal}</p>
            </div>

          </div>
        </div>

      </div>
    </Layout>
  );
}