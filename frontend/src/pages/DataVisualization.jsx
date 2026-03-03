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

  useEffect(() => {
    fetch('http://127.0.0.1:8000/api/data-visualization')
      .then(response => response.json())
      .then(data => {
        if (data.status === 'success') {
          setVizData(data);
        }
        setLoading(false);
      })
      .catch(error => {
        console.error("Fetch Error:", error);
        setLoading(false);
      });
  }, []);

  if (loading) return <Layout activePage="visualization"><div className="flex justify-center items-center h-screen"><p className="animate-pulse">กำลังดึงข้อมูลกราฟเทคนิค...</p></div></Layout>;
  if (!vizData) return <Layout activePage="visualization"><div className="flex justify-center items-center h-screen"><p className="text-red-500">เชื่อมต่อ Backend ไม่ได้</p></div></Layout>;

  const commonOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { position: 'top' } },
    scales: { x: { ticks: { maxTicksLimit: 7 } } } 
  };

  const maData = {
    labels: vizData.labels,
    datasets: [
      { label: 'Price', data: vizData.price_data, borderColor: '#3b82f6', tension: 0.1 },
      { label: 'MA20', data: vizData.ma_data.ma20, borderColor: '#f59e0b', tension: 0.4 }
    ]
  };

  const rsiData = {
    labels: vizData.labels,
    datasets: [{ label: 'RSI', data: vizData.rsi_data, borderColor: '#8b5cf6', tension: 0.1 }]
  };

  const macdData = {
    labels: vizData.labels,
    datasets: [
      { label: 'MACD', data: vizData.macd_data.macd, borderColor: '#3b82f6' },
      { label: 'Signal', data: vizData.macd_data.signal, borderColor: '#ef4444' }
    ]
  };

  const bbData = {
    labels: vizData.labels,
    datasets: [
      { label: 'Price', data: vizData.price_data, borderColor: '#3b82f6' },
      { label: 'Upper', data: vizData.bb_data.upper, borderColor: '#f87171', borderDash: [5,5], pointRadius: 0 },
      { label: 'Lower', data: vizData.bb_data.lower, borderColor: '#34d399', borderDash: [5,5], pointRadius: 0 }
    ]
  };

  // Helper function for dynamic color classes
  const getColorClasses = (theme) => {
    switch (theme) {
      case 'green': return { bg: 'bg-green-50', textMain: 'text-green-600', textSub: 'text-green-500' };
      case 'red': return { bg: 'bg-red-50', textMain: 'text-red-600', textSub: 'text-red-500' };
      case 'yellow': return { bg: 'bg-yellow-50', textMain: 'text-yellow-600', textSub: 'text-yellow-500' };
      case 'blue': return { bg: 'bg-blue-50', textMain: 'text-blue-600', textSub: 'text-blue-500' };
      default: return { bg: 'bg-gray-50', textMain: 'text-gray-600', textSub: 'text-gray-500' };
    }
  };

  const maStyle = getColorClasses(vizData.analysis.ma.color_theme);
  const rsiStyle = getColorClasses(vizData.analysis.rsi.color_theme);
  const macdStyle = getColorClasses(vizData.analysis.macd.color_theme);

  return (
    <Layout activePage="visualization">
      <div className="container mx-auto px-4 pb-10 mt-6">
        
        {/* Charts Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <div className="bg-white p-4 rounded-lg shadow-sm">
            <h3 className="font-semibold mb-2">Moving Averages</h3>
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
          <div className="bg-white p-4 rounded-lg shadow-sm">
            <h3 className="font-semibold mb-2">Bollinger Bands</h3>
            <div className="h-60"><Line data={bbData} options={commonOptions} /></div>
          </div>
        </div>

        {/* Indicator Analysis */}
        <div className="bg-white p-6 rounded-lg shadow-sm">
          <h3 className="font-semibold mb-4 text-lg">การวิเคราะห์ตัวชี้วัดทางเทคนิค (Real-time)</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-center">
            
            <div className={`${maStyle.bg} p-4 rounded`}>
              <p className="font-bold text-gray-700">{vizData.analysis.ma.title}</p>
              <p className={`text-sm ${maStyle.textMain} mt-1`}>{vizData.analysis.ma.value_text}</p>
              <p className={`text-xs ${maStyle.textSub} font-medium mt-1`}>{vizData.analysis.ma.signal}</p>
            </div>
            
            <div className={`${rsiStyle.bg} p-4 rounded`}>
              <p className="font-bold text-gray-700">{vizData.analysis.rsi.title}</p>
              <p className={`text-sm ${rsiStyle.textMain} mt-1`}>{vizData.analysis.rsi.value_text}</p>
              <p className={`text-xs ${rsiStyle.textSub} font-medium mt-1`}>{vizData.analysis.rsi.signal}</p>
            </div>
            
            <div className={`${macdStyle.bg} p-4 rounded`}>
              <p className="font-bold text-gray-700">{vizData.analysis.macd.title}</p>
              <p className={`text-sm ${macdStyle.textMain} mt-1`}>{vizData.analysis.macd.value_text}</p>
              <p className={`text-xs ${macdStyle.textSub} font-medium mt-1`}>{vizData.analysis.macd.signal}</p>
            </div>

          </div>
        </div>

      </div>
    </Layout>
  );
}