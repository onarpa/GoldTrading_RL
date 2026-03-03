import React from 'react';
import { Link } from 'react-router-dom';

export default function Layout({ children, activePage }) {
  return (
    <div className="font-prompt bg-[#f3f4f6] min-h-screen">
      {/* Header */}
      <div className="bg-gradient-to-r from-[#cc9900] to-[#e7cf27] text-white p-4 shadow-lg">
        <div className="container mx-auto flex justify-between items-center">
          <div className="flex items-center space-x-3">
            <div>
              <h1 className="text-xl font-bold">ระบบวิเคราะห์แนวโน้มราคาทองคำ</h1>
              <p className="text-sm opacity-80">Gold Price Trend Analysis System</p>
            </div>
          </div>
          <div className="text-right text-xs opacity-80">
            <p>อัพเดทล่าสุด</p>
            <p>15 ม.ค. 2568 14:30</p>
          </div>
        </div>
      </div>

      {/* Navigation (อัปเดตใช้ Link ของ React Router) */}
      <div className="bg-white shadow-sm mb-6">
        <div className="container mx-auto flex space-x-8 p-4 text-gray-600 font-medium overflow-x-auto">
          <Link 
            to="/dashboard" 
            className={`flex items-center space-x-2 pb-1 ${activePage === 'dashboard' ? 'text-indigo-600 border-b-2 border-indigo-600' : 'hover:text-indigo-600 transition'}`}
          >
            <span>Dashboard</span>
          </Link>
          <Link 
            to="/prediction" 
            className={`flex items-center space-x-2 pb-1 ${activePage === 'prediction' ? 'text-indigo-600 border-b-2 border-indigo-600' : 'hover:text-indigo-600 transition'}`}
          >
            <span>Prediction Result</span>
          </Link>
          <Link 
            to="/performance" 
            className={`flex items-center space-x-2 pb-1 ${activePage === 'performance' ? 'text-indigo-600 border-b-2 border-indigo-600' : 'hover:text-indigo-600 transition'}`}
          >
            <span>Model Performance</span>
          </Link>
          <Link 
            to="/visualization" 
            className={`flex items-center space-x-2 pb-1 ${activePage === 'visualization' ? 'text-indigo-600 border-b-2 border-indigo-600' : 'hover:text-indigo-600 transition'}`}
          >
            <span>Data Visualization</span>
          </Link>
        </div>
      </div>

      {/* Content ของแต่ละหน้าจะมาแทรกตรงนี้ */}
      {children}
    </div>
  );
}