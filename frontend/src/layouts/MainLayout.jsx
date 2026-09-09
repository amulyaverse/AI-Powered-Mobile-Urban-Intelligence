import React, { useState, useEffect, useRef, useCallback } from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  RadioReceiver,
  Map,
  AlertTriangle,
  Activity,
  Settings,
  Bus,
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
  Menu,
  ChevronRight,
} from 'lucide-react';
import { format } from 'date-fns';
import {
  getConnectionState,
  subscribeConnectionState,
  setForceDemoMode,
  checkBackendHealth,
  API_BASE_URL,
} from '../services/api';
import ScrollToTop from '../components/ScrollToTop';
import QuickLinks from '../components/QuickLinks';

const navItems = [
  { path: '/', label: 'Overview', icon: LayoutDashboard },
  { path: '/live', label: 'Live Monitoring', icon: RadioReceiver },
  { path: '/fleet', label: 'Fleet Management', icon: Truck },
  { path: '/events', label: 'Incidents & Events', icon: AlertTriangle },
  { path: '/map', label: 'GIS Map', icon: Map },
  { path: '/traffic', label: 'Traffic Analytics', icon: Activity },
  { path: '/road-conditions', label: 'Road Conditions', icon: Bus },
];

/** Map route paths to human-readable breadcrumb labels */
const breadcrumbMap = {
  '/': 'Overview',
  '/live': 'Live Monitoring',
  '/fleet': 'Fleet Management',
  '/events': 'Incidents & Events',
  '/map': 'GIS Map',
  '/traffic': 'Traffic Analytics',
  '/road-conditions': 'Road Conditions',
};

function Breadcrumbs() {
  const location = useLocation();
  const isRoot = location.pathname === '/';
  if (isRoot) return null;

  const label = breadcrumbMap[location.pathname] ?? 'Page';

  return (
    <nav aria-label="breadcrumb" className="flex items-center gap-1 text-xs text-slate-500">
      <NavLink to="/" className="hover:text-slate-700 transition-colors">
        Home
      </NavLink>
      <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
      <span className="text-slate-700 font-medium">{label}</span>
    </nav>
  );
}

export default function MainLayout() {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [soundAlerts, setSoundAlerts] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [connState, setConnState] = useState(getConnectionState());
  const [isChecking, setIsChecking] = useState(false);
  const [currentTime, setCurrentTime] = useState(new Date());
  const [isScrolled, setIsScrolled] = useState(false);

  const mainRef = useRef(null);
  const location = useLocation();

  // Close mobile menu on route change
  useEffect(() => {
    setIsMobileMenuOpen(false);
  }, [location.pathname]);

  // Scroll-spy for sticky header condensed state
  useEffect(() => {
    const el = mainRef.current;
    if (!el) return;
    const onScroll = () => setIsScrolled(el.scrollTop > 8);
    el.addEventListener('scroll', onScroll, { passive: true });
    return () => el.removeEventListener('scroll', onScroll);
  }, []);

  useEffect(() => {
    const unsub = subscribeConnectionState(setConnState);
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => {
      unsub();
      clearInterval(timer);
    };
  }, []);

  const handleManualHealthCheck = async () => {
    setIsChecking(true);
    await checkBackendHealth();
    setIsChecking(false);
  };

  const closeMobileMenu = useCallback(() => setIsMobileMenuOpen(false), []);

  const toggleSidebar = () => {
    if (window.innerWidth < 768) {
      setIsMobileMenuOpen((prev) => !prev);
    } else {
      setIsSidebarCollapsed((prev) => !prev);
    }
  };

  const getStatusBadge = () => {
    if (connState.status === 'connected') {
      return (
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 shadow-2xs" title={`Connected to ${connState.baseUrl}`}>
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span className="hidden sm:inline">LIVE DATA</span>
        </div>
      );
    }
    if (connState.status === 'offline_fallback') {
      return (
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-800 border border-amber-200 shadow-2xs" title="Backend offline — showing fallback demo data">
          <span className="w-2 h-2 rounded-full bg-amber-500" />
          <span className="hidden sm:inline">DEMO DATA</span>
          <button
            type="button"
            onClick={handleManualHealthCheck}
            disabled={isChecking}
            className="ml-1 text-[11px] underline text-amber-900 hover:text-amber-950 font-medium cursor-pointer hidden sm:inline"
            title="Attempt reconnect to backend"
          >
            {isChecking ? 'Checking...' : 'Reconnect'}
          </button>
        </div>
      );
    }
    return (
      <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-100 text-slate-700 border border-slate-300 shadow-2xs" title="Running in Demo Mode with Mock Data">
        <span className="w-2 h-2 rounded-full bg-slate-400" />
        <span className="hidden sm:inline">DEMO MODE</span>
      </div>
    );
  };

  return (
    <div className="flex h-screen w-full bg-slate-50 font-sans text-slate-900 overflow-hidden">

      {/* ── Mobile overlay backdrop ── */}
      {isMobileMenuOpen && (
        <div
          className="fixed inset-0 bg-slate-900/50 z-30 md:hidden"
          onClick={closeMobileMenu}
          aria-hidden="true"
        />
      )}

      {/* ── Sidebar (desktop: collapsible | mobile: slide-in drawer) ── */}
      <aside
        className={`
          fixed md:static inset-y-0 left-0 z-40
          bg-slate-900 text-white flex flex-col shrink-0
          transition-all duration-300 ease-in-out
          ${isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
          ${isSidebarCollapsed ? 'md:w-16' : 'md:w-64'}
          w-64
        `}
        aria-label="Sidebar navigation"
      >
        {/* Logo / Brand */}
        <div className={`p-4 flex items-center ${isSidebarCollapsed ? 'justify-center' : 'justify-between'} font-semibold text-lg border-b border-slate-700`}>
          <div className="flex items-center gap-3">
            <Bus className="w-6 h-6 text-brand-500 shrink-0" />
            {!isSidebarCollapsed && <span>Urban Intel</span>}
          </div>
          {/* Close button — mobile only */}
          <button
            onClick={closeMobileMenu}
            className="md:hidden text-slate-400 hover:text-white p-1 rounded cursor-pointer"
            aria-label="Close menu"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Nav links */}
        <nav className="flex-1 py-4 flex flex-col gap-1 px-2.5 overflow-y-auto" aria-label="Main navigation">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === '/'}
              title={isSidebarCollapsed ? item.label : undefined}
              className={({ isActive }) =>
                `flex items-center ${isSidebarCollapsed ? 'justify-center px-2' : 'gap-3 px-3'} py-2.5 rounded-md transition-colors text-sm ${
                  isActive
                    ? 'bg-brand-600 text-white shadow-xs'
                    : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                }`
              }
            >
              <item.icon className="w-5 h-5 shrink-0" />
              {!isSidebarCollapsed && <span>{item.label}</span>}
            </NavLink>
          ))}
        </nav>

        {/* Operator info */}
        {!isSidebarCollapsed && (
          <div className="p-4 border-t border-slate-700 text-xs text-slate-400 flex flex-col gap-1">
            <div>Operator: Authority Admin</div>
            <div className="text-[11px] text-slate-500">SIH 2026 Platform v1.0.0</div>
          </div>
        )}
      </aside>

      {/* ── Main Content Area ── */}
      <div className="flex-1 flex flex-col overflow-hidden min-w-0">

        {/* ── Sticky Header ── */}
        <header
          className={`
            bg-white border-b border-slate-200 flex items-center justify-between px-4 md:px-6 shrink-0
            transition-all duration-200 sticky top-0 z-20
            ${isScrolled ? 'h-12 shadow-md' : 'h-14'}
          `}
        >
          {/* Left: universal hamburger button + title + breadcrumbs */}
          <div className="flex items-center gap-3 min-w-0">
            {/* Hamburger Toggle — always visible on both desktop and mobile */}
            <button
              onClick={toggleSidebar}
              className="text-slate-600 hover:text-slate-900 p-1.5 rounded-lg hover:bg-slate-100 transition-colors cursor-pointer shrink-0 flex items-center justify-center border border-slate-200 shadow-2xs"
              aria-label="Toggle navigation sidebar"
              title={isSidebarCollapsed ? "Expand Sidebar" : "Collapse Sidebar"}
            >
              <Menu className="w-5 h-5 text-slate-700" />
            </button>

            <div className="min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <h1 className={`font-semibold text-slate-800 transition-all duration-200 ${isScrolled ? 'text-base' : 'text-lg'}`}>
                  Command Center
                </h1>
                {getStatusBadge()}
              </div>
              {/* Breadcrumbs — below title */}
              <Breadcrumbs />
            </div>
          </div>

          {/* Right: clock + settings + avatar */}
          <div className="flex items-center gap-2 md:gap-4 shrink-0">
            <div className="hidden sm:flex items-center gap-2 px-3 py-1 bg-slate-100/90 rounded-md border border-slate-200 text-xs font-mono text-slate-700 shadow-2xs">
              <Clock className="w-3.5 h-3.5 text-brand-600 animate-pulse shrink-0" />
              <span className="font-semibold whitespace-nowrap">
                {format(currentTime, isScrolled ? 'HH:mm:ss' : 'EEE, dd MMM yyyy • HH:mm:ss')}
              </span>
            </div>
            <button
              onClick={() => setIsSettingsOpen(true)}
              className="text-slate-500 hover:text-slate-800 transition p-1.5 rounded-md hover:bg-slate-100 cursor-pointer"
              title="Platform Settings & Connection"
            >
              <Settings className="w-5 h-5" />
            </button>
            <div className="w-8 h-8 bg-slate-200 rounded-full flex items-center justify-center font-bold text-slate-600 text-xs shadow-inner shrink-0">
              AD
            </div>
          </div>
        </header>

        {/* ── Page Content (scrollable) ── */}
        <main
          ref={mainRef}
          className="flex-1 overflow-y-auto p-4 md:p-6"
        >
          <Outlet />
        </main>

        {/* ── Quick Links Footer ── */}
        <QuickLinks />
      </div>

      {/* ── Back To Top ── */}
      <ScrollToTop scrollContainerRef={mainRef} />

      {/* ── Settings Modal ── */}
      {isSettingsOpen && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-md overflow-hidden border border-slate-200 max-h-[90vh] flex flex-col">
            <div className="p-4 border-b border-slate-200 flex justify-between items-center bg-slate-50 shrink-0">
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

            <div className="p-6 space-y-5 text-sm overflow-y-auto">
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
                    ) : connState.status === 'offline_fallback' ? (
                      <span className="text-amber-700 font-semibold flex items-center gap-1">
                        <WifiOff className="w-3.5 h-3.5 text-amber-600" /> Offline — Using Demo Fallback
                      </span>
                    ) : (
                      <span className="text-slate-500 font-semibold">Checking…</span>
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
                        connState.mode === 'live' ? 'bg-slate-900 text-white' : 'bg-white text-slate-600 border border-slate-200'
                      }`}
                    >
                      Live API
                    </button>
                    <button
                      onClick={() => setForceDemoMode(true)}
                      className={`px-2.5 py-1 rounded font-medium transition cursor-pointer ${
                        connState.mode === 'demo' ? 'bg-brand-600 text-white' : 'bg-white text-slate-600 border border-slate-200'
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

            <div className="p-3 bg-slate-50 border-t border-slate-200 flex justify-end shrink-0">
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
