import React, { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import MainLayout from './layouts/MainLayout';

// Route-level code splitting — each page loads as a separate chunk.
// This keeps the initial JS bundle light on slow mobile connections.
const Overview = lazy(() => import('./pages/Overview'));
const LiveMonitoring = lazy(() => import('./pages/LiveMonitoring'));
const EventPage = lazy(() => import('./pages/EventPage'));
const GISMapPage = lazy(() => import('./pages/GISMapPage'));
const TrafficAnalytics = lazy(() => import('./pages/TrafficAnalytics'));
const RoadAnalytics = lazy(() => import('./pages/RoadAnalytics'));
const FleetManagement = lazy(() => import('./pages/FleetManagement'));

/** Minimal inline fallback shown while a route chunk loads */
function PageFallback() {
  return (
    <div className="flex-1 p-6 space-y-4 animate-pulse">
      {/* Skeleton KPI row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="h-24 rounded-lg bg-slate-200" />
        ))}
      </div>
      {/* Skeleton content rows */}
      <div className="h-64 rounded-lg bg-slate-200" />
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 h-48 rounded-lg bg-slate-200" />
        <div className="h-48 rounded-lg bg-slate-200" />
      </div>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<MainLayout />}>
          <Route
            index
            element={
              <Suspense fallback={<PageFallback />}>
                <Overview />
              </Suspense>
            }
          />
          <Route
            path="live"
            element={
              <Suspense fallback={<PageFallback />}>
                <LiveMonitoring />
              </Suspense>
            }
          />
          <Route
            path="fleet"
            element={
              <Suspense fallback={<PageFallback />}>
                <FleetManagement />
              </Suspense>
            }
          />
          <Route
            path="events"
            element={
              <Suspense fallback={<PageFallback />}>
                <EventPage />
              </Suspense>
            }
          />
          <Route
            path="map"
            element={
              <Suspense fallback={<PageFallback />}>
                <GISMapPage />
              </Suspense>
            }
          />
          <Route
            path="traffic"
            element={
              <Suspense fallback={<PageFallback />}>
                <TrafficAnalytics />
              </Suspense>
            }
          />
          <Route
            path="road-conditions"
            element={
              <Suspense fallback={<PageFallback />}>
                <RoadAnalytics />
              </Suspense>
            }
          />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
