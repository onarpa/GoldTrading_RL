import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import PredictionResult from './pages/PredictionResult';
import ModelPerformance from './pages/ModelPerformance';
import DataVisualization from './pages/DataVisualization';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard"     element={<Dashboard />} />
        <Route path="/prediction"    element={<PredictionResult />} />
        <Route path="/performance"   element={<ModelPerformance />} />
        <Route path="/visualization" element={<DataVisualization />} />
      </Routes>
    </BrowserRouter>
  );
}
