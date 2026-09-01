import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import MainLayout from './layouts/MainLayout';
import Overview from './pages/Overview';
import LiveMonitoring from './pages/LiveMonitoring';
import EventPage from './pages/EventPage';
import GISMapPage from './pages/GISMapPage';
import TrafficAnalytics from './pages/TrafficAnalytics';
import RoadAnalytics from './pages/RoadAnalytics';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<MainLayout />}>
          <Route index element={<Overview />} />
          <Route path="live" element={<LiveMonitoring />} />
          <Route path="events" element={<EventPage />} />
          <Route path="map" element={<GISMapPage />} />
          <Route path="traffic" element={<TrafficAnalytics />} />
          <Route path="road-conditions" element={<RoadAnalytics />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
