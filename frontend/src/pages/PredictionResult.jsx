import React from 'react';
import Layout from '../components/Layout';

export default function PredictionResult() {
  return (
    <Layout activePage="prediction">
      <div className="container mx-auto px-4 pb-10">
        
        {/* การ์ดคาดการณ์ */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white p-6 rounded-lg shadow-sm text-center">
            <h3 className="text-gray-700 font-medium mb-4">การคาดการณ์ 1 วัน</h3>
            <div className="text-2xl font-bold text-green-500 mb-1">ขาขึ้น</div>
            <p className="text-xs text-gray-400 mb-4">ความมั่นใจ: 78%</p>
            <div className="bg-green-100 text-green-700 py-2 rounded font-semibold">BUY</div>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-sm text-center">
            <h3 className="text-gray-700 font-medium mb-4">การคาดการณ์ 7 วัน</h3>
            <div className="text-2xl font-bold text-yellow-500 mb-1">คงที่</div>
            <p className="text-xs text-gray-400 mb-4">ความมั่นใจ: 65%</p>
            <div className="bg-yellow-100 text-yellow-700 py-2 rounded font-semibold">HOLD</div>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-sm text-center">
            <h3 className="text-gray-700 font-medium mb-4">การคาดการณ์ 30 วัน</h3>
            <div className="text-2xl font-bold text-red-500 mb-1">ขาลง</div>
            <p className="text-xs text-gray-400 mb-4">ความมั่นใจ: 72%</p>
            <div className="bg-red-100 text-red-700 py-2 rounded font-semibold">SELL</div>
          </div>
        </div>

        {/* ตารางรายละเอียด */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-8">
          <h3 className="text-lg font-semibold mb-4 text-gray-800">รายละเอียดการคาดการณ์</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-gray-50 text-gray-600 text-sm">
                  <th className="p-4 rounded-tl-lg">วันที่</th>
                  <th className="p-4">ราคาคาดการณ์</th>
                  <th className="p-4">แนวโน้ม</th>
                  <th className="p-4">ความมั่นใจ</th>
                  <th className="p-4 rounded-tr-lg">คำแนะนำ</th>
                </tr>
              </thead>
              <tbody className="text-sm">
                <tr className="border-b">
                  <td className="p-4">16 ก.พ. 2569</td>
                  <td className="p-4 font-medium">2,280 USD</td>
                  <td className="p-4 text-green-500">ขาขึ้น</td>
                  <td className="p-4">78%</td>
                  <td className="p-4"><span className="bg-green-100 text-green-800 px-2 py-1 rounded text-xs">BUY</span></td>
                </tr>
                <tr className="border-b">
                  <td className="p-4">17 ก.พ. 2569</td>
                  <td className="p-4 font-medium">2,285 USD</td>
                  <td className="p-4 text-red-500">ขาลง</td>
                  <td className="p-4">75%</td>
                  <td className="p-4"><span className="bg-red-100 text-red-800 px-2 py-1 rounded text-xs">SELL</span></td>
                </tr>
                <tr>
                  <td className="p-4">18 ก.พ. 2569</td>
                  <td className="p-4 font-medium">2,285 USD</td>
                  <td className="p-4 text-yellow-500">คงที่</td>
                  <td className="p-4">68%</td>
                  <td className="p-4"><span className="bg-yellow-100 text-yellow-800 px-2 py-1 rounded text-xs">HOLD</span></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* การวิเคราะห์ความเสี่ยง */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h3 className="text-lg font-semibold mb-4 text-gray-800">การวิเคราะห์ความเสี่ยง</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div>
              <h4 className="text-gray-700 font-medium mb-2">ปัจจัยเสี่ยงขาขึ้น</h4>
              <ul className="list-disc list-inside text-sm text-red-500 space-y-2">
                <li>การเพิ่มขึ้นของอัตราดอกเบี้ย</li>
                <li>ความแข็งแกร่งของดอลลาร์สหรัฐ</li>
                <li>การขายทำกำไรของนักลงทุน</li>
              </ul>
            </div>
            <div>
              <h4 className="text-gray-700 font-medium mb-2">ปัจจัยสนับสนุนขาขึ้น</h4>
              <ul className="list-disc list-inside text-sm text-green-600 space-y-2">
                <li>ความไม่แน่นอนทางเศรษฐกิจ</li>
                <li>การซื้อของธนาคารกลาง</li>
                <li>อัตราเงินเฟ้อที่สูง</li>
              </ul>
            </div>
          </div>
        </div>

      </div>
    </Layout>
  );
}