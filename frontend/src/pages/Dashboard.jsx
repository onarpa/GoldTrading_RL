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
          <p className="text-xl font-bold text-gray-500 animate-pulse">กำลังดึงข้อมูลตลาดโลก XAU/USD...</p>
        </div>
      </Layout>
    );
  }

  if (!apiData) {
    return (
      <Layout activePage="dashboard">
        <div className="flex justify-center items-center h-screen">
          <p className="text-xl font-bold text-red-500">ไม่สามารถเชื่อมต่อฐานข้อมูลได้</p>
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

  // ส่วนคำนวณราคา Bid/Ask สำหรับ XAUUSD (Gold Spot)
  const basePrice = apiData.current_price;
  
  // กำหนดส่วนต่าง (Spread) แบบสมจริงสำหรับโบรคเกอร์ Forex ทั่วไป (ประมาณ 0.30 USD)
  const spread = 0.30; 
  const bidPrice = basePrice - spread; // ราคา Bid (ราคาที่เรากด Sell ใส่โบรคเกอร์)
  const askPrice = basePrice + spread; // ราคา Ask (ราคาที่เรากด Buy จากโบรคเกอร์)

  return (
    <Layout activePage="dashboard">
      <div className="container mx-auto px-4 pb-10 mt-6">
        
        {/* หัวข้อ Dashboard */}
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-gray-800">XAUUSD (Gold Spot)</h2>
        </div>

        <div className="grid grid-cols-2 lg:grid-cols-6 gap-4 mb-6">
          {/* ราคารับซื้อ (Bid) */}
          <div className="bg-white p-4 rounded-lg shadow-sm border-l-4 border-red-500">
            <p className="text-gray-500 text-xs xl:text-sm">ราคา Bid (Sell)</p>
            <h2 className="text-xl xl:text-2xl font-bold text-gray-800">{bidPrice.toLocaleString(undefined, {minimumFractionDigits: 2})}</h2>
            <p className="text-xs text-gray-400">USD</p>
          </div>

          {/* ราคาขายออก (Ask) */}
          <div className="bg-white p-4 rounded-lg shadow-sm border-l-4 border-green-500">
            <p className="text-gray-500 text-xs xl:text-sm">ราคา Ask (Buy)</p>
            <h2 className="text-xl xl:text-2xl font-bold text-gray-800">{askPrice.toLocaleString(undefined, {minimumFractionDigits: 2})}</h2>
            <p className="text-xs text-gray-400">USD</p>
          </div>

          {/* การเปลี่ยนแปลง */}
          <div className="bg-white p-4 rounded-lg shadow-sm">
            <p className="text-gray-500 text-xs xl:text-sm">การเปลี่ยนแปลง</p>
            <h2 className={`text-xl xl:text-2xl font-bold ${apiData.price_change >= 0 ? 'text-green-500' : 'text-red-500'}`}>
              {apiData.price_change >= 0 ? '+' : ''}{apiData.price_change}
            </h2>
            <p className={`text-xs ${apiData.percent_change >= 0 ? 'text-green-500' : 'text-red-500'}`}>
              {apiData.percent_change >= 0 ? '+' : ''}{apiData.percent_change}%
            </p>
          </div>

          {/* Indicators */}
          <div className="bg-white p-4 rounded-lg shadow-sm">
            <p className="text-gray-500 text-xs xl:text-sm">Indicator (1D)</p>
            <div className="text-xs xl:text-sm font-bold text-gray-800 mt-1">
              RSI: <span className={apiData.technical.rsi > 70 ? 'text-red-500' : apiData.technical.rsi < 30 ? 'text-green-500' : 'text-blue-500'}>{apiData.technical.rsi}</span><br/>
              MACD: <span className={apiData.technical.macd > 0 ? 'text-green-500' : 'text-red-500'}>{apiData.technical.macd}</span>
            </div>
          </div>

          {/* คำแนะนำ (Buy / Hold / Sell) */}
          <div className={`bg-white p-4 rounded-lg shadow-sm border-l-4 ${apiData.recommendation === 'BUY' ? 'border-green-500' : apiData.recommendation === 'SELL' ? 'border-red-500' : 'border-yellow-400'}`}>
            <p className="text-gray-500 text-xs xl:text-sm">แนวโน้มระบบ</p>
            <h2 className={`text-xl xl:text-2xl font-bold ${apiData.recommendation === 'BUY' ? 'text-green-600' : apiData.recommendation === 'SELL' ? 'text-red-600' : 'text-yellow-500'}`}>
              {apiData.recommendation}
            </h2>
          </div>

          {/* ราคาน้ำมันดิบ (Oil Price) */}
          <div className="bg-gray-800 text-white p-4 rounded-lg shadow-sm relative overflow-hidden">
            <div className="relative z-10">
              <p className="text-gray-300 text-xs xl:text-sm">น้ำมันดิบ (WTI)</p>
              <h2 className="text-xl xl:text-2xl font-bold">{apiData.oil.price.toFixed(2)}</h2>
              <p className={`text-xs ${apiData.oil.change >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {apiData.oil.change >= 0 ? '+' : ''}{apiData.oil.change.toFixed(2)} USD
              </p>
            </div>
            <div className="absolute top-2 right-2 text-gray-500 text-[0.6rem] text-right">
              ความสัมพันธ์: <span className="text-green-400">แปรผันตาม</span>
            </div>
          </div>

          {/* ปัจจัยเศรษฐกิจมหภาค (Macroeconomic) */}
          {/* อัตราเงินเฟ้อ (Inflation) */}
          <div className="bg-orange-50 p-4 rounded-lg shadow-sm border border-orange-100 relative">
            <p className="text-orange-700 text-xs xl:text-sm font-semibold">อัตราเงินเฟ้อ (US CPI)</p>
            <h2 className="text-xl xl:text-2xl font-bold text-gray-800">{apiData.macro.inflation}%</h2>
            <p className="text-xs text-orange-600">YoY (Year-over-Year)</p>
            <div className="absolute top-2 right-2 text-gray-500 text-[0.6rem] text-right">
              ความสัมพันธ์: <span className="text-orange-600 font-bold">แปรผันตาม</span>
            </div>
          </div>

          {/* ดอกเบี้ยนโยบายสหรัฐ (FED Rate) */}
          <div className="bg-purple-50 p-4 rounded-lg shadow-sm border border-purple-100 relative">
            <p className="text-purple-700 text-xs xl:text-sm font-semibold">ดอกเบี้ยสหรัฐ (FED Rate)</p>
            <h2 className="text-xl xl:text-2xl font-bold text-gray-800">{apiData.macro.fed_rate}%</h2>
            <p className="text-xs text-purple-600">อัตราดอกเบี้ยอ้างอิง</p>
            <div className="absolute top-2 right-2 text-gray-500 text-[0.6rem] text-right">
              ความสัมพันธ์: <span className="text-purple-600 font-bold">ผกผัน</span>
            </div>
          </div>

          {/* ดัชนีดอลลาร์สหรัฐ (DXY) */}
          <div className="bg-blue-50 p-4 rounded-lg shadow-sm border border-blue-100 relative">
            <p className="text-blue-700 text-xs xl:text-sm font-semibold">ดัชนีดอลลาร์สหรัฐ (DXY)</p>
            <h2 className="text-xl xl:text-2xl font-bold text-gray-800">{apiData.macro.dxy.value}</h2>
            <p className={`text-xs ${apiData.macro.dxy.change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {apiData.macro.dxy.change >= 0 ? '+' : ''}{apiData.macro.dxy.change}
            </p>
            <div className="absolute top-2 right-2 text-gray-500 text-[0.6rem] text-right">
              ความสัมพันธ์: <span className="text-blue-600 font-bold">ผกผัน</span>
            </div>
          </div>
        </div>

        {/* กราฟ */}
        <div className="bg-white p-6 rounded-lg shadow-sm mb-6">
          <h3 className="text-lg font-semibold mb-4 text-gray-800">
            กราฟราคาทองคำตลาดโลกย้อนหลัง 30 วัน (XAU/USD)
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