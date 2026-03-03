import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';

// นำเข้าหน้าเว็บทั้ง 4 หน้า
import Dashboard from './pages/Dashboard';
import PredictionResult from './pages/PredictionResult';
import ModelPerformance from './pages/ModelPerformance';
import DataVisualization from './pages/DataVisualization';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* ตั้งค่าให้หน้าแรกวิ่งไปที่ Dashboard อัตโนมัติ */}
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        
        {/* กำหนดเส้นทาง URL ให้แต่ละหน้า */}
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/prediction" element={<PredictionResult />} />
        <Route path="/performance" element={<ModelPerformance />} />
        <Route path="/visualization" element={<DataVisualization />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;