import React, { useState, useEffect } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import {
  LayoutDashboard,
  RadioReceiver,
  Map,
  AlertTriangle,
  Activity,
  Settings,
  Bus,
  X,
  Shield,
  Server,
  Bell,
  Sliders,
  RefreshCw,
  Database,
  Wifi,
  WifiOff,
} from 'lucide-react';
import {
  getConnectionState,
  subscribeConnectionState,
  setForceDemoMode,
  checkBackendHealth,
  API_BASE_URL,
} from '../services/api';

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
  const [connState, setConnState] = useState(getConnectionState());
  const [isChecking, setIsChecking] = useState(false);

  useEffect(() => {
    const unsub = subscribeConnectionState(setConnState);
    return unsub;
  }, []);

  const handleManualHealthCheck = async () => {
    setIsChecking(true);
    await checkBackendHealth();
    setIsChecking(false);
  };

  const getStatusBadge = () => {
    if (connState.status === 'connected') {
      return (
        <div
          className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 shadow-2xs"
          title={`Connected to ${connState.baseUrl}`}
        >
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
          <span>LIVE DATA</span>
        </div>
      );
    }
    if (connState.status === 'offline_fallback') {
      return (
        <div
          className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-800 border border-amber-200 shadow-2xs"
          title={`Backend offline (${connState.errorMessage || connState.baseUrl}) — Showing Demo Data`}
        >
          <span className="w-2 h-2 rounded-full bg-amber-500"></span>
          <span>DEMO DATA (OFFLINE)</span>
        </div>
      );
    }
    return (
      <div
        className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-100 text-slate-700 border border-slate-300 shadow-2xs"
        title="Running in Demo Mode with Mock Data"
      >
        <span className="w-2 h-2 rounded-full bg-slate-400"></span>
        <span>DEMO MODE</span>
      </div>
    );
  };

  return (
    <div className="flex h-screen w-full bg-slate-50 font-sans text-slate-900">
      {/* Sidebar */}
      <aside className="w-64 bg-slate-900 text-white flex flex-col shrink-0">
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
                  isActive
                    ? 'bg-brand-600 text-white'
                    : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                }`
              }
            >
              <item.icon className="w-5 h-5" />
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>
        <div className="p-4 border-t border-slate-700 text-xs text-slate-400 flex flex-col gap-1">
          <div>Operator: Authority Admin</div>
          <div className="text-[11px] text-slate-500">SIH 2026 Platform v1.0.0</div>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="h-14 bg-white border-b border-slate-200 flex items-center justify-between px-6 shrink-0">
          <div className="flex items-center gap-3">
            <h1 className="font-semibold text-lg text-slate-800">Command Center</h1>
            {getStatusBadge()}
          </div>
          <div className="flex items-center gap-4">
            <button
              onClick={() => setIsSettingsOpen(true)}
              className="text-slate-500 hover:text-slate-800 transition p-1.5 rounded-md hover:bg-slate-100 cursor-pointer"
              title="Platform Settings & Connection"
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
          <div className="bg-white rounded-lg shadow-xl w-full max-w-md overflow-hidden border border-slate-200">
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
              {/* Connection Status Section */}
              <div>
                <h4 className="font-semibold text-slate-800 mb-2 flex items-center justify-between">
                  <span className="flex items-center gap-2">
                    <Server className="w-4 h-4 text-brand-600" />
                    API Gateway Status
                  </span>
                  <button
                    onClick={handleManualHealthCheck}
                    disabled={isChecking}
                    className="text-xs text-brand-600 hover:text-brand-800 flex items-center gap-1 font-medium cursor-pointer"
                  >
                    <RefreshCw className={`w-3 h-3 ${isChecking ? 'animate-spin' : ''}`} />
                    Test Connection
                  </button>
                </h4>
                <div className="p-3 bg-slate-50 rounded border border-slate-200 font-mono text-xs text-slate-600 break-all space-y-1">
                  <div>
                    <span className="text-slate-400 font-sans">URL:</span> {API_BASE_URL}
                  </div>
                  <div className="flex items-center gap-2 pt-1">
                    <span className="text-slate-400 font-sans">State:</span>
                    {connState.status === 'connected' ? (
                      <span className="text-emerald-700 font-semibold flex items-center gap-1">
                        <Wifi className="w-3.5 h-3.5 text-emerald-600" /> Live Backend Online
                      </span>
                    ) : (
                      <span className="text-amber-700 font-semibold flex items-center gap-1">
                        <WifiOff className="w-3.5 h-3.5 text-amber-600" /> Offline — Using Demo Fallback
                      </span>
                    )}
                  </div>
                </div>
              </div>

              {/* Data Mode Switcher */}
              <div className="bg-slate-50 p-3 rounded-lg border border-slate-200 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-slate-700 flex items-center gap-1.5">
                    <Database className="w-4 h-4 text-brand-600" />
                    Data Mode
                  </span>
                  <div className="flex gap-1 text-xs">
                    <button
                      onClick={() => setForceDemoMode(false)}
                      className={`px-2.5 py-1 rounded font-medium transition cursor-pointer ${
                        connState.mode === 'live'
                          ? 'bg-slate-900 text-white'
                          : 'bg-white text-slate-600 border border-slate-200'
                      }`}
                    >
                      Live API
                    </button>
                    <button
                      onClick={() => setForceDemoMode(true)}
                      className={`px-2.5 py-1 rounded font-medium transition cursor-pointer ${
                        connState.mode === 'demo'
                          ? 'bg-brand-600 text-white'
                          : 'bg-white text-slate-600 border border-slate-200'
                      }`}
                    >
                      Demo Data
                    </button>
                  </div>
                </div>
                <p className="text-[11px] text-slate-500">
                  {connState.mode === 'live'
                    ? 'Requests target the backend API and fallback to mock data if unreachable.'
                    : 'All requests use local mock data without attempting network requests.'}
                </p>
              </div>

              {/* Inference Config */}
              <div>
                <h4 className="font-semibold text-slate-800 mb-2 flex items-center gap-2">
                  <Sliders className="w-4 h-4 text-brand-600" />
                  Inference & Telemetry
                </h4>
                <div className="space-y-2 text-slate-600 text-xs">
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

              {/* Preferences */}
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
                <span>SIH 2026</span>
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
