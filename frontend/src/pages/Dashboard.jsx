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
  const [selectedType, setSelectedType] = useState('bar');
  const [apiData, setApiData] = useState(null);
  const [loading, setLoading] = useState(true);

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

  if (loading) {
    return (
      <Layout activePage="dashboard">
        <div className="flex justify-center items-center h-screen">
          <p className="text-xl font-bold text-gray-500 animate-pulse">กำลังดึงข้อมูลตลาดโลกล่าสุด...</p>
        </div>
      </Layout>
    );
  }

  if (!apiData) {
    return (
      <Layout activePage="dashboard">
        <div className="flex justify-center items-center h-screen">
          <p className="text-xl font-bold text-red-500">ไม่สามารถเชื่อมต่อฐานข้อมูลได้ กรุณาตรวจสอบ Backend</p>
        </div>
      </Layout>
    );
  }

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
    scales: { x: { ticks: { maxTicksLimit: 10 } } }
  };

  // ส่วนคำนวณราคาจริงให้เป็น "รับซื้อ" และ "ขายออก"
  // สำหรับทองรูปพรรณจำลองให้ราคาสูงกว่าแท่ง 50 USD
  const priceOffset = selectedType === 'ornament' ? 50 : 0; 
  const basePrice = apiData.current_price + priceOffset;
  
  // กำหนดส่วนต่าง (Spread) ของตลาดโลกประมาณ 0.50 USD ต่อฝั่ง
  const spread = 0.50; 
  const buyPrice = basePrice - spread; // ราคารับซื้อ
  const sellPrice = basePrice + spread; // ราคาขายออก

  return (
    <Layout activePage="dashboard">
      <div className="container mx-auto px-4 pb-10 mt-6">
        
        {/* Toggle ประเภททอง */}
        <div className="mb-4">
          <div className="bg-white rounded-lg shadow-sm inline-flex overflow-hidden border border-gray-200">
            <button 
              onClick={() => setSelectedType('bar')}
              className={`px-6 py-3 text-sm font-medium border-r ${selectedType === 'bar' ? 'bg-indigo-600 text-white' : 'hover:bg-gray-100 text-gray-700'}`}>
              ทองคำแท่ง (อ้างอิง USD)
            </button>
            <button 
              onClick={() => setSelectedType('ornament')}
              className={`px-6 py-3 text-sm font-medium ${selectedType === 'ornament' ? 'bg-indigo-600 text-white' : 'hover:bg-gray-100 text-gray-700'}`}>
              ทองรูปพรรณ (อ้างอิง USD)
            </button>
          </div>
        </div>

        {/* ปรับ Grid เป็น 6 คอลัมน์ สำหรับรองรับรับซื้อ/ขายออก */}
        <div className="grid grid-cols-2 lg:grid-cols-6 gap-4 mb-6">
          
          {/* 1. ราคารับซื้อ */}
          <div className="bg-white p-4 rounded-lg shadow-sm border-l-4 border-blue-500">
            <p className="text-gray-500 text-xs xl:text-sm">ราคารับซื้อ (Bid)</p>
            <h2 className="text-xl xl:text-2xl font-bold text-gray-800">{buyPrice.toLocaleString(undefined, {minimumFractionDigits: 2})}</h2>
            <p className="text-xs text-gray-400">USD</p>
          </div>

          {/* 2. ราคาขายออก */}
          <div className="bg-white p-4 rounded-lg shadow-sm border-l-4 border-indigo-500">
            <p className="text-gray-500 text-xs xl:text-sm">ราคาขายออก (Ask)</p>
            <h2 className="text-xl xl:text-2xl font-bold text-gray-800">{sellPrice.toLocaleString(undefined, {minimumFractionDigits: 2})}</h2>
            <p className="text-xs text-gray-400">USD</p>
          </div>

          {/* 3. การเปลี่ยนแปลง */}
          <div className="bg-white p-4 rounded-lg shadow-sm">
            <p className="text-gray-500 text-xs xl:text-sm">การเปลี่ยนแปลง</p>
            <h2 className={`text-xl xl:text-2xl font-bold ${apiData.price_change >= 0 ? 'text-green-500' : 'text-red-500'}`}>
              {apiData.price_change >= 0 ? '+' : ''}{apiData.price_change}
            </h2>
            <p className={`text-xs ${apiData.percent_change >= 0 ? 'text-green-500' : 'text-red-500'}`}>
              {apiData.percent_change >= 0 ? '+' : ''}{apiData.percent_change}%
            </p>
          </div>

          {/* 4. Indicators */}
          <div className="bg-white p-4 rounded-lg shadow-sm">
            <p className="text-gray-500 text-xs xl:text-sm">อินดิเคเตอร์</p>
            <div className="text-xs xl:text-sm font-bold text-gray-800 mt-1">
              RSI: <span className={apiData.technical.rsi > 70 ? 'text-red-500' : apiData.technical.rsi < 30 ? 'text-green-500' : 'text-blue-500'}>{apiData.technical.rsi}</span><br/>
              MACD: <span className={apiData.technical.macd > 0 ? 'text-green-500' : 'text-red-500'}>{apiData.technical.macd}</span>
            </div>
          </div>

          {/* 5. คำแนะนำ */}
          <div className="bg-white p-4 rounded-lg shadow-sm border-l-4 border-yellow-400">
            <p className="text-gray-500 text-xs xl:text-sm">คำแนะนำ</p>
            <h2 className={`text-xl xl:text-2xl font-bold ${apiData.recommendation === 'BUY' ? 'text-green-600' : apiData.recommendation === 'SELL' ? 'text-red-600' : 'text-yellow-500'}`}>
              {apiData.recommendation}
            </h2>
          </div>

          {/* 6. ราคาน้ำมัน */}
          <div className="bg-gray-800 text-white p-4 rounded-lg shadow-sm">
            <p className="text-gray-300 text-xs xl:text-sm">น้ำมันดิบ (WTI)</p>
            <h2 className="text-xl xl:text-2xl font-bold">{apiData.oil.price.toFixed(2)}</h2>
            <p className={`text-xs ${apiData.oil.change >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              {apiData.oil.change >= 0 ? '+' : ''}{apiData.oil.change.toFixed(2)} USD
            </p>
          </div>
        </div>

        {/* กราฟ */}
        <div className="bg-white p-6 rounded-lg shadow-sm mb-6">
          <h3 className="text-lg font-semibold mb-4 text-gray-800">
            กราฟราคาทองคำตลาดโลกย้อนหลัง 30 วัน (USD)
          </h3>
          <div className="h-72">
            <Line data={chartData} options={chartOptions} />
          </div>
        </div>

        {/* สถิติสำคัญ */}
        <div className="bg-white p-6 rounded-lg shadow-sm">
            <h3 className="text-lg font-bold mb-4 text-gray-800">สถิติสำคัญ</h3>
            <div className="flex flex-col space-y-4">
              <div className="flex justify-between items-center border-b pb-3">
                <span className="text-gray-600 text-sm md:text-base">ราคาสูงสุด (52 สัปดาห์)</span>
                <span className="font-bold text-gray-900">{apiData.statistics.high_52w.toLocaleString(undefined, {minimumFractionDigits: 2})} USD</span>
              </div>
              <div className="flex justify-between items-center border-b pb-3">
                <span className="text-gray-600 text-sm md:text-base">ราคาต่ำสุด (52 สัปดาห์)</span>
                <span className="font-bold text-gray-900">{apiData.statistics.low_52w.toLocaleString(undefined, {minimumFractionDigits: 2})} USD</span>
              </div>
              <div className="flex justify-between items-center border-b pb-3">
                <span className="text-gray-600 text-sm md:text-base">ค่าเฉลี่ย (30 วัน)</span>
                <span className="font-bold text-gray-900">{apiData.statistics.avg_30d.toLocaleString(undefined, {minimumFractionDigits: 2})} USD</span>
              </div>
              <div className="flex justify-between items-center pb-1">
                <span className="text-gray-600 text-sm md:text-base">ความผันผวน (30 วัน)</span>
                <span className="font-bold text-gray-900">{apiData.statistics.volatility_30d.toFixed(2)}%</span>
              </div>
            </div>
        </div>

      </div>
    </Layout>
  );
}