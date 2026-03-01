import React from 'react';
import Layout from '../components/Layout';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS, CategoryScale, LinearScale, PointElement,
  LineElement, Title, Tooltip, Legend
} from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

export default function DataVisualization() {
  const labels = Array.from({length: 20}, (_, i) => i + 1);

  // การตั้งค่า Options กลางสำหรับทุกกราฟ
  const commonOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { position: 'top' } }
  };

  const maData = {
    labels,
    datasets: [
      { label: 'Price', data: [40,41,39,42,41,40,39,38,39,40,41,42,41,40,39,38,37,36,35,34], borderColor: '#3b82f6', tension: 0.1 },
      { label: 'MA20', data: [41,41,41,40,40,40,40,39,39,39,39,38,38,38,38,37,37,36,36,35], borderColor: '#f59e0b', tension: 0.4 }
    ]
  };

  const rsiData = {
    labels,
    datasets: [{ label: 'RSI', data: [60,45,65,45,60,40,65,55,60,68,50,35,55,38,65,55,50,68,65,30], borderColor: '#8b5cf6', tension: 0.1 }]
  };

  const macdData = {
    labels,
    datasets: [
      { label: 'MACD', data: [-50, 90, -40, -70, -20, 80, -30, 0, 40, -90, 20, -80, 0, 80, -60, 40, -50, 60, -40, -80], borderColor: '#3b82f6' },
      { label: 'Signal', data: [-40, 40, -20, -30, -40, 70, -30, -10, 40, -10, 25, -70, -10, 60, -40, 30, -40, 40, -40, -60], borderColor: '#ef4444' }
    ]
  };

  const bbData = {
    labels,
    datasets: [
      { label: 'Price', data: [4200,4210,4240,4260,4250,4280,4320,4300,4320,4310,4280,4290,4310,4350,4370,4360,4340,4350,4330,4300], borderColor: '#3b82f6' },
      { label: 'Upper', data: [4250,4260,4300,4330,4300,4350,4380,4350,4370,4360,4330,4340,4360,4400,4420,4410,4390,4400,4380,4350], borderColor: '#f87171', borderDash: [5,5], pointRadius: 0 },
      { label: 'Lower', data: [4150,4160,4200,4220,4200,4240,4250,4240,4270,4250,4210,4220,4240,4280,4300,4290,4280,4290,4270,4250], borderColor: '#34d399', borderDash: [5,5], pointRadius: 0 }
    ]
  };

  return (
    <Layout activePage="visualization">
      <div className="container mx-auto px-4 pb-10">
        
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
          <h3 className="font-semibold mb-4 text-lg">การวิเคราะห์ตัวชี้วัดทางเทคนิค</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-center">
            <div className="bg-green-50 p-4 rounded">
              <p className="font-bold text-gray-700">Moving Average</p>
              <p className="text-sm text-green-600 mt-1">ราคาอยู่เหนือ MA20 และ MA50</p>
              <p className="text-xs text-green-500">สัญญาณขาขึ้น</p>
            </div>
            <div className="bg-yellow-50 p-4 rounded">
              <p className="font-bold text-gray-700">RSI</p>
              <p className="text-sm text-yellow-600 mt-1">RSI = 58.2</p>
              <p className="text-xs text-yellow-500">อยู่ในเขตกลาง</p>
            </div>
            <div className="bg-blue-50 p-4 rounded">
              <p className="font-bold text-gray-700">MACD</p>
              <p className="text-sm text-blue-600 mt-1">MACD เหนือ Signal Line</p>
              <p className="text-xs text-blue-500">สัญญาณบวก</p>
            </div>
          </div>
        </div>

      </div>
    </Layout>
  );
}