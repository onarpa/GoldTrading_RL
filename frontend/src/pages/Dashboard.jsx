import React, { useState, useEffect } from 'react';
import Layout from '../components/Layout';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS, CategoryScale, LinearScale, PointElement,
  LineElement, Title, Tooltip, Filler
} from 'chart.js';

// Setup Chart.js
ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Filler);

export default function Dashboard() {
  // สร้าง State เพื่อเก็บข้อมูลที่ดึงมาจาก Backend
  const [apiData, setApiData] = useState(null);
  const [loading, setLoading] = useState(true);

  // ดึงข้อมูลจาก FastAPI ทันทีที่โหลดหน้านี้
  useEffect(() => {
    fetch('http://127.0.0.1:8000/api/dashboard-data')
      .then(response => response.json())
      .then(data => {
        if (data.status === 'success') {
          setApiData(data);
        } else {
          console.error("API Error:", data.message);
        }
        setLoading(false);
      })
      .catch(error => {
        console.error("Fetch Error:", error);
        setLoading(false);
      });
  }, []);

  // หน้าจอตอนกำลังโหลดข้อมูล
  if (loading) {
    return (
      <Layout activePage="dashboard">
        <div className="flex justify-center items-center h-screen">
          <p className="text-xl font-bold text-gray-500 animate-pulse">กำลังดึงข้อมูลราคาทองคำตลาดโลก...</p>
        </div>
      </Layout>
    );
  }

  // หน้าจอตอนดึงข้อมูลไม่สำเร็จ
  if (!apiData) {
    return (
      <Layout activePage="dashboard">
        <div className="flex justify-center items-center h-screen">
          <p className="text-xl font-bold text-red-500">ไม่สามารถดึงข้อมูลได้ กรุณาตรวจสอบว่า Backend ทำงานอยู่หรือไม่</p>
        </div>
      </Layout>
    );
  }

  // ตั้งค่าข้อมูลกราฟโดยใช้ข้อมูลจาก API
  const chartData = {
    labels: apiData.chart_labels,
    datasets: [{
      label: 'ราคาปิด XAU/USD (USD)',
      data: apiData.chart_data,
      borderColor: '#3b82f6',
      backgroundColor: 'rgba(59,130,246,0.1)',
      fill: true,
      tension: 0.4
    }]
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: {
        x: { ticks: { maxTicksLimit: 10 } } 
    }
  };

  return (
    <Layout activePage="dashboard">
      <div className="container mx-auto px-4 pb-10">
        
        <div className="mb-4">
          <div className="bg-indigo-600 text-white rounded-lg shadow-sm inline-flex px-6 py-3 font-medium">
            ราคาทองคำตลาดโลก (XAU/USD)
          </div>
        </div>

        {/* ข้อมูลสถิติแบบ Real-time จาก API */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white p-5 rounded-lg shadow-sm">
            <p className="text-gray-500 text-sm">ราคาปัจจุบัน (Close)</p>
            <h2 className="text-3xl font-bold">{apiData.current_price.toLocaleString()}</h2>
            <p className="text-xs text-gray-400">USD / Ounce</p>
          </div>

          <div className="bg-white p-5 rounded-lg shadow-sm">
            <p className="text-gray-500 text-sm">การเปลี่ยนแปลง (วันต่อวัน)</p>
            <h2 className={`text-3xl font-bold ${apiData.price_change >= 0 ? 'text-green-500' : 'text-red-500'}`}>
              {apiData.price_change >= 0 ? '+' : ''}{apiData.price_change}
            </h2>
            <p className={`text-xs ${apiData.percent_change >= 0 ? 'text-green-500' : 'text-red-500'}`}>
              USD ({apiData.percent_change >= 0 ? '+' : ''}{apiData.percent_change}%)
            </p>
          </div>

          <div className="bg-white p-5 rounded-lg shadow-sm">
            <p className="text-gray-500 text-sm">อินดิเคเตอร์หลัก</p>
            <p className="text-sm font-bold text-gray-800 mt-1">RSI: <span className={apiData.technical.rsi > 70 ? 'text-red-500' : apiData.technical.rsi < 30 ? 'text-green-500' : 'text-blue-500'}>{apiData.technical.rsi}</span></p>
            <p className="text-sm font-bold text-gray-800">MACD: <span className={apiData.technical.macd > 0 ? 'text-green-500' : 'text-red-500'}>{apiData.technical.macd}</span></p>
            <p className="text-sm font-bold text-gray-800">EMA(20): <span className="text-yellow-600">{apiData.technical.ema_20}</span></p>
          </div>

          <div className="bg-white p-5 rounded-lg shadow-sm border-l-4 border-indigo-500">
            <p className="text-gray-500 text-sm">คำแนะนำจากระบบเบื้องต้น</p>
            <h2 className={`text-3xl font-bold ${apiData.recommendation === 'BUY' ? 'text-green-600' : apiData.recommendation === 'SELL' ? 'text-red-600' : 'text-yellow-500'}`}>
              {apiData.recommendation}
            </h2>
            <p className="text-xs text-gray-400 mt-1">อ้างอิงจาก MACD และ RSI</p>
          </div>
        </div>

        {/* กราฟ */}
        <div className="bg-white p-6 rounded-lg shadow-sm mb-6">
          <h3 className="text-lg font-semibold mb-4 text-gray-800">กราฟราคาทองคำย้อนหลัง 30 วันทำการ</h3>
          <div className="h-72">
            <Line data={chartData} options={chartOptions} />
          </div>
        </div>

      </div>
    </Layout>
  );
}