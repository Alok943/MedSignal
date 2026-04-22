import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import LandingPage from './pages/LandingPage';
import Analysis from './pages/Analysis';
import DemoCases from './pages/DemoCases';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/"         element={<LandingPage />} />
        <Route path="/analysis" element={<Analysis />} />
        <Route path="/demo"     element={<DemoCases />} />
      </Routes>
    </BrowserRouter>
  );
}