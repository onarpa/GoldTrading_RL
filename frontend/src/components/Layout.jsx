import React from 'react';
import { Link, useLocation } from 'react-router-dom';

export default function Layout({ children }) {
  const location = useLocation();
  const path = location.pathname;

  const navItems = [
    { href: '/dashboard',      label: 'Dashboard' },
    { href: '/prediction',     label: 'Prediction Result' },
    { href: '/performance',    label: 'Model Performance' },
    { href: '/visualization',  label: 'Data Visualization' },
  ];

  return (
    <div className="font-sans bg-[#f3f4f6] min-h-screen">
      {/* Header */}
      <div className="bg-gradient-to-r from-[#cc9900] to-[#e7cf27] text-white p-4 shadow-lg">
        <div className="container mx-auto flex justify-between items-center">
          <div>
            <h1 className="text-xl font-bold">ระบบวิเคราะห์แนวโน้มราคาทองคำ</h1>
            <p className="text-sm opacity-80">Gold Price Trend Analysis — RL Agent</p>
          </div>
          <div className="text-right text-xs opacity-80">
            <p>อัพเดทล่าสุด</p>
            <p>{new Date().toLocaleString('th-TH')}</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <div className="bg-white shadow-sm mb-6">
        <div className="container mx-auto flex space-x-8 p-4 text-gray-600 font-medium overflow-x-auto">
          {navItems.map(({ href, label }) => (
            <Link
              key={href}
              to={href}
              className={`flex items-center space-x-2 pb-1 whitespace-nowrap transition ${
                path === href
                  ? 'text-indigo-600 border-b-2 border-indigo-600'
                  : 'hover:text-indigo-600'
              }`}
            >
              <span>{label}</span>
            </Link>
          ))}
        </div>
      </div>

      {children}
    </div>
  );
}
