import React, { useState, useEffect } from 'react';
import Layout from '../components/Layout';

export default function PredictionResult() {
  const [predData, setPredData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://127.0.0.1:8000/api/prediction-result')
      .then(res => res.json())
      .then(data => {
        if (data.status === 'success') {
          setPredData(data);
        }
        setLoading(false);
      })
      .catch(err => {
        console.error("Fetch Error:", err);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <Layout activePage="prediction">
        <div className="flex justify-center items-center h-screen">
          <p className="animate-pulse text-lg font-bold text-gray-600">กำลังวิเคราะห์และทำนายแนวโน้มตลาด...</p>
        </div>
      </Layout>
    );
  }

  if (!predData) {
    return (
      <Layout activePage="prediction">
        <div className="flex justify-center items-center h-screen text-red-500 font-bold">
          ไม่สามารถเชื่อมต่อได้
        </div>
      </Layout>
    );
  }

  // ฟังก์ชันตัวช่วยกำหนดสีตาม Action (BUY, SELL, HOLD)
  const getStyle = (action) => {
    if (action === 'BUY') return { text: 'text-green-500', bg: 'bg-green-100', badgeText: 'text-green-700', border: 'border-green-500' };
    if (action === 'SELL') return { text: 'text-red-500', bg: 'bg-red-100', badgeText: 'text-red-700', border: 'border-red-500' };
    return { text: 'text-yellow-500', bg: 'bg-yellow-100', badgeText: 'text-yellow-700', border: 'border-yellow-500' };
  };

  const { summary, daily_predictions, risk_analysis } = predData;

  return (
    <Layout activePage="prediction">
      <div className="container mx-auto px-4 pb-10 mt-6">
        
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-gray-800">ผลการคาดการณ์ (Prediction Result)</h2>
        </div>

        {/* การ์ดคาดการณ์ (Summary) */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          
          <div className={`bg-white p-6 rounded-lg shadow-sm text-center border-t-4 ${getStyle(summary.day_1.action).border}`}>
            <h3 className="text-gray-700 font-medium mb-4">การคาดการณ์ 1 วัน</h3>
            <div className={`text-2xl font-bold ${getStyle(summary.day_1.action).text} mb-1`}>{summary.day_1.trend}</div>
            <p className="text-xs text-gray-400 mb-4">ความมั่นใจ: {summary.day_1.confidence}%</p>
            <div className={`${getStyle(summary.day_1.action).bg} ${getStyle(summary.day_1.action).badgeText} py-2 rounded font-semibold`}>
              {summary.day_1.action}
            </div>
          </div>

          <div className={`bg-white p-6 rounded-lg shadow-sm text-center border-t-4 ${getStyle(summary.day_7.action).border}`}>
            <h3 className="text-gray-700 font-medium mb-4">การคาดการณ์ 7 วัน</h3>
            <div className={`text-2xl font-bold ${getStyle(summary.day_7.action).text} mb-1`}>{summary.day_7.trend}</div>
            <p className="text-xs text-gray-400 mb-4">ความมั่นใจ: {summary.day_7.confidence}%</p>
            <div className={`${getStyle(summary.day_7.action).bg} ${getStyle(summary.day_7.action).badgeText} py-2 rounded font-semibold`}>
              {summary.day_7.action}
            </div>
          </div>

          <div className={`bg-white p-6 rounded-lg shadow-sm text-center border-t-4 ${getStyle(summary.day_30.action).border}`}>
            <h3 className="text-gray-700 font-medium mb-4">การคาดการณ์ 30 วัน</h3>
            <div className={`text-2xl font-bold ${getStyle(summary.day_30.action).text} mb-1`}>{summary.day_30.trend}</div>
            <p className="text-xs text-gray-400 mb-4">ความมั่นใจ: {summary.day_30.confidence}%</p>
            <div className={`${getStyle(summary.day_30.action).bg} ${getStyle(summary.day_30.action).badgeText} py-2 rounded font-semibold`}>
              {summary.day_30.action}
            </div>
          </div>

        </div>

        {/* ตารางรายละเอียดรายวัน */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-8">
          <h3 className="text-lg font-semibold mb-4 text-gray-800">รายละเอียดการคาดการณ์ล่วงหน้า 5 วัน</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-gray-50 text-gray-600 text-sm border-b">
                  <th className="p-4 font-semibold">วันที่</th>
                  <th className="p-4 font-semibold">ราคาคาดการณ์</th>
                  <th className="p-4 font-semibold">แนวโน้ม</th>
                  <th className="p-4 font-semibold">ความมั่นใจ</th>
                  <th className="p-4 font-semibold">คำแนะนำ</th>
                </tr>
              </thead>
              <tbody className="text-sm">
                {daily_predictions.map((day, index) => (
                  <tr key={index} className="border-b hover:bg-gray-50 transition">
                    <td className="p-4">{day.date}</td>
                    <td className="p-4 font-medium text-gray-800">{day.price}</td>
                    <td className={`p-4 font-bold ${getStyle(day.action).text}`}>{day.trend}</td>
                    <td className="p-4 text-gray-600">{day.confidence}</td>
                    <td className="p-4">
                      <span className={`${getStyle(day.action).bg} ${getStyle(day.action).badgeText} px-3 py-1 rounded-full text-xs font-bold`}>
                        {day.action}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* การวิเคราะห์ความเสี่ยง */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h3 className="text-lg font-semibold mb-4 text-gray-800">การวิเคราะห์ปัจจัยความเสี่ยง</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            
            <div className="bg-red-50 p-5 rounded-lg border border-red-100">
              <h4 className="text-red-700 font-bold mb-3 flex items-center">
                <span className="mr-2"></span> ปัจจัยกดดันราคา (Downside Risks)
              </h4>
              <ul className="list-disc list-inside text-sm text-red-600 space-y-2">
                {risk_analysis.downside_risks.map((risk, idx) => (
                  <li key={idx}>{risk}</li>
                ))}
              </ul>
            </div>
            
            <div className="bg-green-50 p-5 rounded-lg border border-green-100">
              <h4 className="text-green-700 font-bold mb-3 flex items-center">
                <span className="mr-2"></span> ปัจจัยสนับสนุนราคา (Upside Supports)
              </h4>
              <ul className="list-disc list-inside text-sm text-green-600 space-y-2">
                {risk_analysis.upside_supports.map((support, idx) => (
                  <li key={idx}>{support}</li>
                ))}
              </ul>
            </div>

          </div>
        </div>

      </div>
    </Layout>
  );
}