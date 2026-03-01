import React from 'react';
import Layout from '../components/Layout';
import { Line, Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS, CategoryScale, LinearScale, PointElement,
  LineElement, BarElement, Title, Tooltip, Filler
} from 'chart.js';

// ลงทะเบียน Component ของ ChartJS (รวม BarElement สำหรับกราฟแท่ง)
ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, BarElement, Title, Tooltip, Filler);

export default function ModelPerformance() {
  const months = ['ม.ค.', 'ก.พ.', 'มี.ค.', 'เม.ย.', 'พ.ค.', 'มิ.ย.', 'ก.ค.', 'ส.ค.', 'ก.ย.', 'ต.ค.', 'พ.ย.', 'ธ.ค.'];

  const returnChartData = {
    labels: months,
    datasets: [{
      label: 'Return',
      data: [0, 2.2, 0.4, -0.2, -0.6, 3.3, 1.1, -1.0, 2.6, 4.0, 3.7, 5.8],
      borderColor: '#10b981',
      backgroundColor: 'rgba(16, 185, 129, 0.1)',
      fill: true,
      tension: 0.4
    }]
  };

  const monthlyChartData = {
    labels: months,
    datasets: [{
      label: 'Monthly %',
      data: [2.1, -0.8, 3.5, 1.2, -1.5, 2.8, 0.9, 3.2, -0.5, 1.8, 3.8, 5.2],
      backgroundColor: (context) => {
        const value = context.dataset.data[context.dataIndex];
        return value >= 0 ? '#10b981' : '#ef4444'; // สีเขียวถ้าบวก แดงถ้าลบ
      }
    }]
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false } }
  };

  return (
    <Layout activePage="performance">
      <div className="container mx-auto px-4 pb-10">
        
        {/* Metric Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white p-5 rounded-lg shadow-sm">
            <p className="text-gray-500 text-xs uppercase">Accuracy</p>
            <h2 className="text-3xl font-bold text-green-500">78.5%</h2>
            <p className="text-xs text-gray-400">ความแม่นยำโมเดล</p>
          </div>
          <div className="bg-white p-5 rounded-lg shadow-sm">
            <p className="text-gray-500 text-xs uppercase">Sharpe Ratio</p>
            <h2 className="text-3xl font-bold text-blue-500">1.42</h2>
            <p className="text-xs text-gray-400">อัตราส่วนความเสี่ยง</p>
          </div>
          <div className="bg-white p-5 rounded-lg shadow-sm">
            <p className="text-gray-500 text-xs uppercase">Win Rate</p>
            <h2 className="text-3xl font-bold text-purple-500">72.3%</h2>
            <p className="text-xs text-gray-400">อัตราการชนะ</p>
          </div>
          <div className="bg-white p-5 rounded-lg shadow-sm">
            <p className="text-gray-500 text-xs uppercase">Max Drawdown</p>
            <h2 className="text-3xl font-bold text-red-500">-8.2%</h2>
            <p className="text-xs text-gray-400">การสูญเสียสูงสุด</p>
          </div>
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <div className="bg-white p-6 rounded-lg shadow-sm">
            <h3 className="text-sm font-semibold mb-4 text-gray-800">Cumulative Return</h3>
            <div className="h-64"><Line data={returnChartData} options={chartOptions} /></div>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-sm">
            <h3 className="text-sm font-semibold mb-4 text-gray-800">Monthly Performance</h3>
            <div className="h-64"><Bar data={monthlyChartData} options={chartOptions} /></div>
          </div>
        </div>

        {/* Table */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h3 className="text-lg font-semibold mb-4 text-gray-800">สถิติประสิทธิภาพรายเดือน</h3>
          <table className="w-full text-left">
            <thead className="text-xs text-gray-400 uppercase border-b">
              <tr>
                <th className="py-3">เดือน</th>
                <th className="py-3">Return (%)</th>
                <th className="py-3">Accuracy (%)</th>
                <th className="py-3">Win Rate (%)</th>
                <th className="py-3">Trades</th>
              </tr>
            </thead>
            <tbody className="text-sm text-gray-600">
              <tr className="border-b">
                <td className="py-3">ม.ค. 2569</td>
                <td className="text-green-500 font-medium">+5.2%</td>
                <td>82.1%</td>
                <td>75.0%</td>
                <td>24</td>
              </tr>
              <tr className="border-b">
                <td className="py-3">ธ.ค. 2568</td>
                <td className="text-green-500 font-medium">+3.8%</td>
                <td>79.3%</td>
                <td>71.4%</td>
                <td>21</td>
              </tr>
              <tr>
                <td className="py-3">พ.ย. 2568</td>
                <td className="text-red-500 font-medium">-1.5%</td>
                <td>74.2%</td>
                <td>68.2%</td>
                <td>22</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </Layout>
  );
}