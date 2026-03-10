import React, { useState, useEffect } from 'react';
import Layout from '../components/Layout';
import { Line, Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS, CategoryScale, LinearScale, PointElement,
  LineElement, BarElement, Title, Tooltip, Filler, Legend
} from 'chart.js';

// ลงทะเบียน Component ของกราฟ (เพิ่ม BarElement สำหรับกราฟแท่ง)
ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, BarElement, Title, Tooltip, Filler, Legend);

export default function ModelPerformance() {
  const [perfData, setPerfData] = useState(null);
  const [loading, setLoading] = useState(true);

  // ดึงข้อมูลประสิทธิภาพโมเดลจาก API
  useEffect(() => {
    fetch('http://127.0.0.1:8000/api/model-performance')
      .then(response => response.json())
      .then(data => {
        if (data.status === 'success') {
          setPerfData(data);
        }
        setLoading(false);
      })
      .catch(error => {
        console.error("Fetch Error:", error);
        setLoading(false);
      });
  }, []);

  if (loading) return <Layout activePage="performance"><div className="flex justify-center items-center h-screen"><p className="animate-pulse text-xl text-gray-500 font-bold">กำลังประมวลผลประสิทธิภาพ AI...</p></div></Layout>;
  if (!perfData) return <Layout activePage="performance"><div className="flex justify-center items-center h-screen"><p className="text-red-500 font-bold">ไม่สามารถดึงข้อมูลได้</p></div></Layout>;

  // 1. ตั้งค่ากราฟผลตอบแทนสะสม (Cumulative Return) - กราฟเส้น
  const cumulativeChartData = {
    labels: perfData.cumulative_chart.labels,
    datasets: [{
      label: 'ผลตอบแทนสะสม (%)',
      data: perfData.cumulative_chart.data,
      borderColor: '#8b5cf6', // สีม่วง
      backgroundColor: 'rgba(139, 92, 246, 0.1)',
      fill: true,
      tension: 0.4
    }]
  };

  // 2. ตั้งค่ากราฟผลงานรายเดือน (Monthly Performance) - กราฟแท่ง
  const monthlyChartData = {
    labels: perfData.monthly_chart.labels,
    datasets: [{
      label: 'ผลตอบแทนรายเดือน (%)',
      data: perfData.monthly_chart.data,
      // ถ้าค่าเป็นบวกให้เป็นสีเขียว ถ้าติดลบให้เป็นสีแดง
      backgroundColor: perfData.monthly_chart.data.map(val => val >= 0 ? 'rgba(34, 197, 94, 0.8)' : 'rgba(239, 68, 68, 0.8)'),
      borderRadius: 4
    }]
  };

  // Option ทั่วไปสำหรับกราฟ
  const commonOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false } }
  };

  return (
    <Layout activePage="performance">
      <div className="container mx-auto px-4 pb-10 mt-6">
        
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-gray-800">ประสิทธิภาพของโมเดล (Model Performance)</h2>
        </div>

        {/* 1. สถิติสำคัญ 4 กล่อง (Cards) */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white p-5 rounded-lg shadow-sm border-t-4 border-blue-500">
            <p className="text-gray-500 text-sm">ความแม่นยำ (Accuracy)</p>
            <h2 className="text-3xl font-bold text-blue-600">{perfData.metrics.accuracy}%</h2>
          </div>
          <div className="bg-white p-5 rounded-lg shadow-sm border-t-4 border-purple-500">
            <p className="text-gray-500 text-sm">อัตราส่วนผลตอบแทนต่อความเสี่ยง (Sharpe Ratio)</p>
            <h2 className="text-3xl font-bold text-purple-600">{perfData.metrics.sharpe_ratio}</h2>
          </div>
          <div className="bg-white p-5 rounded-lg shadow-sm border-t-4 border-green-500">
            <p className="text-gray-500 text-sm">อัตราการชนะ (Win Rate)</p>
            <h2 className="text-3xl font-bold text-green-600">{perfData.metrics.win_rate}%</h2>
          </div>
          <div className="bg-white p-5 rounded-lg shadow-sm border-t-4 border-red-500">
            <p className="text-gray-500 text-sm">การสูญเสียสูงสุด (Max Drawdown)</p>
            <h2 className="text-3xl font-bold text-red-600">{perfData.metrics.max_drawdown}%</h2>
          </div>
        </div>

        {/* 2. กราฟ 2 ตัว (เรียงซ้ายขวาในจอคอม) */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          {/* กราฟ Cumulative */}
          <div className="bg-white p-6 rounded-lg shadow-sm">
            <h3 className="text-lg font-bold mb-4 text-gray-800">ผลตอบแทนสะสม (Cumulative Return)</h3>
            <div className="h-64">
              <Line data={cumulativeChartData} options={commonOptions} />
            </div>
          </div>
          
          {/* กราฟ Monthly */}
          <div className="bg-white p-6 rounded-lg shadow-sm">
            <h3 className="text-lg font-bold mb-4 text-gray-800">ผลตอบแทนรายเดือน (Monthly Return)</h3>
            <div className="h-64">
              <Bar data={monthlyChartData} options={commonOptions} />
            </div>
          </div>
        </div>

        {/* 3. ตารางสถิติรายเดือน */}
        <div className="bg-white rounded-lg shadow-sm overflow-hidden">
          <div className="p-6 border-b">
            <h3 className="text-lg font-bold text-gray-800">สถิติประสิทธิภาพรายเดือน (Monthly Statistics)</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-gray-50 text-gray-600 text-sm border-b">
                  <th className="p-4 font-semibold">เดือน</th>
                  <th className="p-4 font-semibold">Return (%)</th>
                  <th className="p-4 font-semibold">Accuracy (%)</th>
                  <th className="p-4 font-semibold">Win Rate (%)</th>
                  <th className="p-4 font-semibold">Trades (ครั้ง)</th>
                </tr>
              </thead>
              <tbody>
                {perfData.table_data.map((row, index) => (
                  <tr key={index} className="border-b hover:bg-gray-50 transition">
                    <td className="p-4 font-medium text-gray-800">{row.month}</td>
                    <td className={`p-4 font-bold ${row.return >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {row.return >= 0 ? '+' : ''}{row.return}%
                    </td>
                    <td className="p-4 text-gray-700">{row.accuracy}%</td>
                    <td className="p-4 text-gray-700">{row.win_rate}%</td>
                    <td className="p-4 text-gray-700">{row.trades}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

      </div>
    </Layout>
  );
}