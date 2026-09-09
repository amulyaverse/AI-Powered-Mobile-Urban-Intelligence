import React, { useState, useEffect, useRef } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import {
  LayoutDashboard,
  RadioReceiver,
  Map,
  AlertTriangle,
  Activity,
  Settings,
  Truck,
  X,
  Shield,
  Server,
  Bell,
  Sliders,
  RefreshCw,
  Database,
  Wifi,
  WifiOff,
  Clock,
  ChevronDown,
  Bus,
} from 'lucide-react';
import { format } from 'date-fns';
import {
  getConnectionState,
  subscribeConnectionState,
  setForceDemoMode,
  checkBackendHealth,
  API_BASE_URL,
} from '../services/api';

const navItems = [
  { path: '/',               label: 'Overview',         icon: LayoutDashboard },
  { path: '/live',           label: 'Live Monitor',     icon: RadioReceiver },
  { path: '/fleet',          label: 'Fleet',            icon: Truck },
  { path: '/events',         label: 'Incidents',        icon: AlertTriangle },
  { path: '/map',            label: 'GIS Map',          icon: Map },
  { path: '/traffic',        label: 'Traffic',          icon: Activity },
  { path: '/road-conditions',label: 'Road Conditions',  icon: Bus },
];

/* ── Status Badge ──────────────────────────────────────────────── */
function StatusBadge({ connState, isChecking, onReconnect }) {
  if (connState.status === 'connected') {
    return (
      <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-bold bg-gis-sage-light text-gis-sage-dark border border-gis-sage/30 select-none">
        <span className="w-1.5 h-1.5 rounded-full bg-gis-sage animate-pulse" />
        <span className="hidden sm:inline">LIVE</span>
      </div>
    );
  }
  if (connState.status === 'offline_fallback') {
    return (
      <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-bold bg-gis-amber-light text-gis-amber border border-gis-amber/30 select-none">
        <span className="w-1.5 h-1.5 rounded-full bg-gis-amber" />
        <span className="hidden sm:inline">DEMO</span>
        <button
          type="button"
          onClick={onReconnect}
          disabled={isChecking}
          className="ml-0.5 text-[10px] underline opacity-70 hover:opacity-100 cursor-pointer font-semibold"
        >
          {isChecking ? '…' : 'Reconnect'}
        </button>
      </div>
    );
  }
  return (
    <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-bold bg-gis-slate-light text-gis-slate-dark border border-gis-slate/20 select-none">
      <span className="w-1.5 h-1.5 rounded-full bg-gis-slate" />
      <span className="hidden sm:inline">DEMO</span>
    </div>
  );
}

/* ── Settings Modal ────────────────────────────────────────────── */
function SettingsModal({ connState, isChecking, onCheck, onClose,
  confidenceThreshold, setConfidenceThreshold,
  clusterRadius, setClusterRadius,
  pollingInterval, setPollingInterval,
  autoRefresh, setAutoRefresh,
  soundAlerts, setSoundAlerts,
}) {
  return (
    <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center z-[200] p-4">
      <div className="glass-card rounded-3xl shadow-float w-full max-w-md overflow-hidden border border-gis-border">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gis-border flex justify-between items-center bg-gis-slate-light/50">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-2xl bg-gis-blue/10 flex items-center justify-center">
              <Settings className="w-4 h-4 text-gis-blue" />
            </div>
            <h3 className="font-bold text-slate-800 text-sm">Platform Settings</h3>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full flex items-center justify-center text-slate-400 hover:text-slate-700 hover:bg-gis-slate-light transition-all duration-150 cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="p-6 space-y-5 text-sm">
          {/* API Status */}
          <div>
            <h4 className="font-bold text-slate-700 mb-2 flex items-center justify-between text-xs uppercase tracking-wide">
              <span className="flex items-center gap-2">
                <Server className="w-3.5 h-3.5 text-gis-blue" />
                API Gateway
              </span>
              <button
                onClick={onCheck}
                disabled={isChecking}
                className="flex items-center gap-1 text-gis-blue hover:text-gis-blue-dark font-semibold cursor-pointer normal-case tracking-normal"
              >
                <RefreshCw className={`w-3 h-3 ${isChecking ? 'animate-spin' : ''}`} />
                Test
              </button>
            </h4>
            <div className="p-3 bg-gis-slate-light/60 rounded-2xl border border-gis-border font-mono text-xs text-slate-600 space-y-1.5">
              <div><span className="text-slate-400 font-sans font-medium">URL </span>{API_BASE_URL}</div>
              <div className="flex items-center gap-2 pt-0.5">
                <span className="text-slate-400 font-sans font-medium">State </span>
                {connState.status === 'connected' ? (
                  <span className="text-gis-sage-dark font-bold flex items-center gap-1">
                    <Wifi className="w-3.5 h-3.5 text-gis-sage" /> Live Online
                  </span>
                ) : connState.status === 'offline_fallback' ? (
                  <span className="text-gis-amber font-bold flex items-center gap-1">
                    <WifiOff className="w-3.5 h-3.5" /> Offline — Demo Fallback
                  </span>
                ) : (
                  <span className="text-slate-500 font-bold">Checking…</span>
                )}
              </div>
            </div>
          </div>

          {/* Data Mode */}
          <div className="bg-gis-slate-light/50 p-4 rounded-2xl border border-gis-border space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-bold text-slate-700 text-xs flex items-center gap-1.5 uppercase tracking-wide">
                <Database className="w-3.5 h-3.5 text-gis-blue" /> Data Mode
              </span>
              <div className="flex gap-1 text-xs bg-white rounded-xl p-0.5 border border-gis-border shadow-sm">
                <button
                  onClick={() => setForceDemoMode(false)}
                  className={`px-3 py-1 rounded-xl font-bold transition-all duration-150 cursor-pointer ${
                    connState.mode === 'live'
                      ? 'bg-gis-blue text-white shadow-sm'
                      : 'text-slate-500 hover:text-slate-700'
                  }`}
                >Live</button>
                <button
                  onClick={() => setForceDemoMode(true)}
                  className={`px-3 py-1 rounded-xl font-bold transition-all duration-150 cursor-pointer ${
                    connState.mode === 'demo'
                      ? 'bg-gis-sage text-white shadow-sm'
                      : 'text-slate-500 hover:text-slate-700'
                  }`}
                >Demo</button>
              </div>
            </div>
            <p className="text-[11px] text-slate-500 leading-relaxed">
              {connState.mode === 'live'
                ? 'Requests target the backend API and fallback to mock data if unreachable.'
                : 'All requests use local mock data without attempting network requests.'}
            </p>
          </div>

          {/* Inference Config — Interactive Controls */}
          <div>
            <h4 className="font-bold text-slate-700 mb-3 flex items-center gap-2 text-xs uppercase tracking-wide">
              <Sliders className="w-3.5 h-3.5 text-gis-blue" /> Inference & Telemetry
            </h4>
            <div className="space-y-4 bg-gis-slate-light/40 rounded-2xl p-4 border border-gis-border">
              {/* Confidence Threshold */}
              <div>
                <div className="flex justify-between items-center mb-1.5">
                  <label className="text-xs font-semibold text-slate-600">Min Confidence Threshold</label>
                  <span className="text-xs font-extrabold text-gis-blue bg-gis-blue-light px-2 py-0.5 rounded-lg">
                    {confidenceThreshold}%
                  </span>
                </div>
                <input
                  type="range" min={30} max={95} step={5}
                  value={confidenceThreshold}
                  onChange={(e) => setConfidenceThreshold(Number(e.target.value))}
                  className="w-full h-1.5 rounded-full appearance-none cursor-pointer accent-gis-blue bg-gis-border"
                />
                <div className="flex justify-between text-[10px] text-slate-400 mt-0.5">
                  <span>30%</span><span>95%</span>
                </div>
              </div>

              {/* Hotspot Cluster Radius */}
              <div>
                <div className="flex justify-between items-center mb-1.5">
                  <label className="text-xs font-semibold text-slate-600">Hotspot Cluster Radius</label>
                  <span className="text-xs font-extrabold text-gis-sage bg-gis-sage-light px-2 py-0.5 rounded-lg">
                    {clusterRadius}m
                  </span>
                </div>
                <input
                  type="range" min={20} max={200} step={10}
                  value={clusterRadius}
                  onChange={(e) => setClusterRadius(Number(e.target.value))}
                  className="w-full h-1.5 rounded-full appearance-none cursor-pointer accent-gis-sage bg-gis-border"
                />
                <div className="flex justify-between text-[10px] text-slate-400 mt-0.5">
                  <span>20m</span><span>200m</span>
                </div>
              </div>

              {/* GPS Polling Interval */}
              <div>
                <div className="flex justify-between items-center mb-1.5">
                  <label className="text-xs font-semibold text-slate-600">GPS Telemetry Polling</label>
                  <span className="text-xs font-extrabold text-gis-slate bg-gis-slate-light px-2 py-0.5 rounded-lg">
                    {pollingInterval}s
                  </span>
                </div>
                <input
                  type="range" min={2} max={30} step={1}
                  value={pollingInterval}
                  onChange={(e) => setPollingInterval(Number(e.target.value))}
                  className="w-full h-1.5 rounded-full appearance-none cursor-pointer accent-gis-slate bg-gis-border"
                />
                <div className="flex justify-between text-[10px] text-slate-400 mt-0.5">
                  <span>2s</span><span>30s</span>
                </div>
              </div>
            </div>
          </div>

          {/* Preferences */}
          <div className="border-t border-gis-border pt-4">
            <h4 className="font-bold text-slate-700 mb-3 flex items-center gap-2 text-xs uppercase tracking-wide">
              <Bell className="w-3.5 h-3.5 text-gis-blue" /> Preferences
            </h4>
            <div className="space-y-2.5">
              {[
                { label: 'Live Auto-Refresh Polling', value: autoRefresh, set: setAutoRefresh },
                { label: 'Audio Alerts on Critical Hotspots', value: soundAlerts, set: setSoundAlerts },
              ].map(({ label, value, set }) => (
                <label key={label} className="flex items-center justify-between cursor-pointer group">
                  <span className="text-slate-600 group-hover:text-slate-800 transition-colors text-xs">{label}</span>
                  <button
                    type="button"
                    onClick={() => set(!value)}
                    className={`w-10 h-5 rounded-full relative transition-all duration-200 cursor-pointer shrink-0 ${value ? 'bg-gis-sage' : 'bg-gis-border'}`}
                  >
                    <div className={`w-4 h-4 bg-white rounded-full shadow-sm absolute top-0.5 transition-all duration-200 ${value ? 'left-5' : 'left-0.5'}`} />
                  </button>
                </label>
              ))}
            </div>
          </div>

          <div className="border-t border-gis-border pt-3 flex items-center justify-between text-xs text-slate-400">
            <span className="flex items-center gap-1.5">
              <Shield className="w-3.5 h-3.5 text-gis-sage" /> Operator: Authority Admin
            </span>
            <span className="font-semibold text-gis-slate">NagarNet v1.0</span>
          </div>
        </div>

        <div className="px-6 py-4 bg-gis-slate-light/40 border-t border-gis-border flex justify-end">
          <button
            onClick={onClose}
            className="px-5 py-2 bg-gis-blue text-white rounded-xl font-bold text-sm hover:bg-gis-blue-dark transition-all duration-150 shadow-sm cursor-pointer"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

/* ── Main Layout ───────────────────────────────────────────────── */
export default function MainLayout() {
  const [isSettingsOpen, setIsSettingsOpen]   = useState(false);
  const [connState, setConnState]             = useState(getConnectionState());
  const [isChecking, setIsChecking]           = useState(false);
  const [currentTime, setCurrentTime]         = useState(new Date());
  const [navCollapsed, setNavCollapsed]       = useState(false);
  const lastScrollY                           = useRef(0);

  // Inference controls — persisted in state, readable by child components if needed
  const [confidenceThreshold, setConfidenceThreshold] = useState(65);
  const [clusterRadius, setClusterRadius]             = useState(50);
  const [pollingInterval, setPollingInterval]         = useState(5);
  const [autoRefresh, setAutoRefresh]                 = useState(true);
  const [soundAlerts, setSoundAlerts]                 = useState(true);

  useEffect(() => {
    const unsub  = subscribeConnectionState(setConnState);
    const timer  = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => { unsub(); clearInterval(timer); };
  }, []);

  // Auto-collapse navbar on scroll down, reveal on scroll up
  useEffect(() => {
    const onScroll = () => {
      const main = document.getElementById('gis-main-scroll');
      if (!main) return;
      const y = main.scrollTop;
      setNavCollapsed(y > lastScrollY.current && y > 80);
      lastScrollY.current = y;
    };
    const el = document.getElementById('gis-main-scroll');
    el?.addEventListener('scroll', onScroll, { passive: true });
    return () => el?.removeEventListener('scroll', onScroll);
  }, []);

  const handleManualHealthCheck = async () => {
    setIsChecking(true);
    await checkBackendHealth();
    setIsChecking(false);
  };

  return (
    <div className="flex flex-col h-screen w-full bg-gis-bg font-nunito text-slate-900 overflow-hidden">

      {/* ── Floating Top Navbar ──────────────────────────────────── */}
      <header
        className={`
          gis-navbar fixed top-0 left-0 right-0 z-[100]
          bg-white/80 border-b border-gis-border/60 shadow-nav
          transition-all duration-300 ease-in-out
          ${navCollapsed ? '-translate-y-full opacity-0 pointer-events-none' : 'translate-y-0 opacity-100'}
        `}
      >
        <div className="max-w-screen-2xl mx-auto px-4 sm:px-6 h-16 flex items-center gap-3">

          {/* Brand */}
          <div className="flex items-center gap-2.5 shrink-0 mr-2">
            <div className="w-9 h-9 rounded-2xl bg-gradient-to-br from-gis-blue to-gis-blue-dark flex items-center justify-center shadow-sm">
              <Map className="w-5 h-5 text-white" />
            </div>
            <div className="hidden sm:block">
              <div className="font-extrabold text-sm text-slate-800 leading-tight">NagarNet</div>
              <div className="text-[10px] text-gis-slate font-semibold leading-tight">City Intelligence</div>
            </div>
          </div>

          {/* Nav Pills */}
          <nav className="flex items-center gap-1 flex-1 overflow-x-auto no-scrollbar py-1">
            {navItems.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                end={item.path === '/'}
                className={({ isActive }) =>
                  `flex items-center gap-1.5 px-3 py-2 rounded-full text-xs font-bold whitespace-nowrap transition-all duration-200 select-none cursor-pointer
                  ${isActive
                    ? 'bg-gis-blue text-white shadow-sm scale-[1.03]'
                    : 'text-slate-500 hover:text-gis-blue-dark hover:bg-gis-blue-light/60 hover:scale-[1.02]'
                  }`
                }
              >
                <item.icon className="w-3.5 h-3.5 shrink-0" />
                <span className="hidden md:inline">{item.label}</span>
              </NavLink>
            ))}
          </nav>

          {/* Right Controls */}
          <div className="flex items-center gap-2 shrink-0 ml-2">
            {/* Clock */}
            <div className="hidden lg:flex items-center gap-1.5 px-3 py-1.5 bg-gis-slate-light rounded-full border border-gis-border text-xs font-mono text-slate-600 font-semibold">
              <Clock className="w-3 h-3 text-gis-blue" />
              <span>{format(currentTime, 'HH:mm:ss')}</span>
            </div>

            {/* Status badge */}
            <StatusBadge
              connState={connState}
              isChecking={isChecking}
              onReconnect={handleManualHealthCheck}
            />

            {/* Settings */}
            <button
              onClick={() => setIsSettingsOpen(true)}
              className="w-9 h-9 rounded-full flex items-center justify-center text-slate-400 hover:text-gis-blue hover:bg-gis-blue-light/60 transition-all duration-200 cursor-pointer"
              title="Platform Settings"
            >
              <Settings className="w-4 h-4" />
            </button>

            {/* Avatar */}
            <div className="w-9 h-9 rounded-full bg-gradient-to-br from-gis-blue-light to-gis-sage-light border border-gis-border flex items-center justify-center font-extrabold text-gis-blue text-xs shadow-sm select-none">
              AD
            </div>
          </div>
        </div>
      </header>

      {/* Collapsed-nav reveal tab */}
      {navCollapsed && (
        <button
          onClick={() => setNavCollapsed(false)}
          className="fixed top-2 left-1/2 -translate-x-1/2 z-[101] flex items-center gap-1.5 px-4 py-1.5 bg-white/90 backdrop-blur-sm rounded-full shadow-nav border border-gis-border text-xs font-bold text-gis-blue hover:bg-gis-blue hover:text-white transition-all duration-200 cursor-pointer"
        >
          <ChevronDown className="w-3.5 h-3.5 rotate-180" />
          Show Nav
        </button>
      )}

      {/* ── Page Content ────────────────────────────────────────── */}
      <main
        id="gis-main-scroll"
        className="flex-1 overflow-y-auto pt-16"
      >
        <div className="max-w-screen-2xl mx-auto px-4 sm:px-6 py-6">
          <Outlet />
        </div>
      </main>

      {/* ── Settings Modal ───────────────────────────────────────── */}
      {isSettingsOpen && (
        <SettingsModal
          connState={connState}
          isChecking={isChecking}
          onCheck={handleManualHealthCheck}
          onClose={() => setIsSettingsOpen(false)}
          confidenceThreshold={confidenceThreshold} setConfidenceThreshold={setConfidenceThreshold}
          clusterRadius={clusterRadius}             setClusterRadius={setClusterRadius}
          pollingInterval={pollingInterval}         setPollingInterval={setPollingInterval}
          autoRefresh={autoRefresh}                 setAutoRefresh={setAutoRefresh}
          soundAlerts={soundAlerts}                 setSoundAlerts={setSoundAlerts}
        />
      )}
    </div>
  );
}
