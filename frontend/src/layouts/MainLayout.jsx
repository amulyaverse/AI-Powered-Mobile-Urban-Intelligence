import React, { useState } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { LayoutDashboard, RadioReceiver, Map, AlertTriangle, Activity, Settings, Bus, X, Shield, Server, Bell, Sliders } from 'lucide-react';

const navItems = [
  { path: '/', label: 'Overview', icon: LayoutDashboard },
  { path: '/live', label: 'Live Monitoring', icon: RadioReceiver },
  { path: '/events', label: 'Incidents & Events', icon: AlertTriangle },
  { path: '/map', label: 'GIS Map', icon: Map },
  { path: '/traffic', label: 'Traffic Analytics', icon: Activity },
  { path: '/road-conditions', label: 'Road Conditions', icon: Bus },
];

export default function MainLayout() {
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [soundAlerts, setSoundAlerts] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);

  return (
    <div className="flex h-screen w-full bg-slate-50 font-sans text-slate-900">
      {/* Sidebar */}
      <aside className="w-64 bg-slate-900 text-white flex flex-col">
        <div className="p-4 flex items-center gap-3 font-semibold text-lg border-b border-slate-700">
          <Bus className="w-6 h-6 text-brand-500" />
          <span>Urban Intel</span>
        </div>
        <nav className="flex-1 py-4 flex flex-col gap-1 px-3">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-md transition-colors ${
                  isActive ? 'bg-brand-600 text-white' : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                }`
              }
            >
              <item.icon className="w-5 h-5" />
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>
        <div className="p-4 border-t border-slate-700 text-sm text-slate-400">
          Operator: Authority Admin
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="h-14 bg-white border-b border-slate-200 flex items-center justify-between px-6">
          <h1 className="font-semibold text-lg text-slate-800">Command Center</h1>
          <div className="flex items-center gap-4">
            <button
              onClick={() => setIsSettingsOpen(true)}
              className="text-slate-500 hover:text-slate-800 transition p-1 rounded-md hover:bg-slate-100 cursor-pointer"
              title="Platform Settings"
            >
              <Settings className="w-5 h-5" />
            </button>
            <div className="w-8 h-8 bg-slate-200 rounded-full flex items-center justify-center font-bold text-slate-600 text-xs shadow-inner">
              AD
            </div>
          </div>
        </header>
        
        {/* Page Content */}
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>

      {/* Settings Modal */}
      {isSettingsOpen && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-md overflow-hidden animate-in fade-in zoom-in-95 duration-150 border border-slate-200">
            <div className="p-4 border-b border-slate-200 flex justify-between items-center bg-slate-50">
              <div className="flex items-center gap-2">
                <Settings className="w-5 h-5 text-slate-700" />
                <h3 className="font-bold text-slate-800">Platform Settings</h3>
              </div>
              <button
                onClick={() => setIsSettingsOpen(false)}
                className="text-slate-400 hover:text-slate-700 p-1 rounded hover:bg-slate-200 cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6 space-y-5 text-sm">
              <div>
                <h4 className="font-semibold text-slate-800 mb-2 flex items-center gap-2">
                  <Server className="w-4 h-4 text-brand-600" />
                  API Gateway
                </h4>
                <div className="p-3 bg-slate-50 rounded border border-slate-200 font-mono text-xs text-slate-600 break-all">
                  {import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}
                </div>
              </div>

              <div>
                <h4 className="font-semibold text-slate-800 mb-2 flex items-center gap-2">
                  <Sliders className="w-4 h-4 text-brand-600" />
                  Inference & Telemetry
                </h4>
                <div className="space-y-2 text-slate-600">
                  <div className="flex justify-between items-center">
                    <span>Min Confidence Threshold:</span>
                    <span className="font-semibold text-slate-800">65% (0.65)</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>Hotspot Cluster Radius:</span>
                    <span className="font-semibold text-slate-800">50 meters</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>GPS Telemetry Polling:</span>
                    <span className="font-semibold text-slate-800">5 seconds</span>
                  </div>
                </div>
              </div>

              <div className="border-t border-slate-200 pt-4 space-y-3">
                <h4 className="font-semibold text-slate-800 mb-2 flex items-center gap-2">
                  <Bell className="w-4 h-4 text-brand-600" />
                  Preferences
                </h4>
                <label className="flex items-center justify-between cursor-pointer">
                  <span className="text-slate-700">Live Auto-Refresh Polling</span>
                  <input
                    type="checkbox"
                    checked={autoRefresh}
                    onChange={(e) => setAutoRefresh(e.target.checked)}
                    className="rounded text-brand-600 focus:ring-brand-500 w-4 h-4"
                  />
                </label>
                <label className="flex items-center justify-between cursor-pointer">
                  <span className="text-slate-700">Audio alerts on Critical Hotspots</span>
                  <input
                    type="checkbox"
                    checked={soundAlerts}
                    onChange={(e) => setSoundAlerts(e.target.checked)}
                    className="rounded text-brand-600 focus:ring-brand-500 w-4 h-4"
                  />
                </label>
              </div>

              <div className="border-t border-slate-200 pt-4 flex items-center justify-between text-xs text-slate-500">
                <span className="flex items-center gap-1">
                  <Shield className="w-3.5 h-3.5 text-emerald-600" /> Operator: Authority Admin
                </span>
                <span>SIH 2026 v1.0.0</span>
              </div>
            </div>

            <div className="p-3 bg-slate-50 border-t border-slate-200 flex justify-end">
              <button
                onClick={() => setIsSettingsOpen(false)}
                className="px-4 py-2 bg-slate-900 text-white rounded font-medium text-xs hover:bg-slate-800 transition cursor-pointer"
              >
                Close Settings
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

