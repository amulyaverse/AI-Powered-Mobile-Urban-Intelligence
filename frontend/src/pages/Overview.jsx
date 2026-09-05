import React, { useEffect, useState, useCallback } from 'react';
import { getKPIMetrics, getEvents, getSystemAlerts } from '../services/api';
import { Activity, AlertTriangle, MapPin, Truck, Sparkles } from 'lucide-react';
import AlertPanel from '../components/AlertPanel';
import MiniMap from '../components/MiniMap';
import { LoadingState, ErrorState } from '../components/PageStatusState';

export default function Overview() {
  const [metrics, setMetrics] = useState(null);
  const [recentEvents, setRecentEvents] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadData = useCallback(async (isInitial = false) => {
    if (isInitial) setLoading(true);
    try {
      const [m, e, a] = await Promise.all([
        getKPIMetrics(),
        getEvents({ limit: 20 }),
        getSystemAlerts(),
      ]);
      setMetrics(m);
      setRecentEvents(e || []);
      setAlerts(a || []);
      setError(null);
    } catch (err) {
      console.error('[Overview] Failed to load data:', err);
      setError(err.message || 'Unable to connect to backend.');
    } finally {
      if (isInitial) setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData(true);
    // Poll every 10 seconds for live updates
    const interval = setInterval(() => loadData(false), 10_000);
    return () => clearInterval(interval);
  }, [loadData]);

  if (loading && !metrics) {
    return <LoadingState message="Loading urban intelligence overview..." />;
  }

  if (error && !metrics) {
    return (
      <ErrorState
        title="Command Center Unavailable"
        message="Could not load platform metrics. You can retry the connection or switch to Demo Mode."
        onRetry={() => loadData(true)}
      />
    );
  }

  const safeMetrics = metrics || {
    activeBuses: 0,
    eventsToday: 0,
    potholesDetected: 0,
    criticalAlerts: 0,
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-slate-800">Platform Overview</h2>
          <p className="text-xs text-slate-500">Real-time mobile sensing and intelligence aggregated across active fleet</p>
        </div>
      </div>
      
      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard title="Active Buses" value={safeMetrics.activeBuses} icon={Truck} color="text-blue-600" bg="bg-blue-100" />
        <KPICard title="Events Today" value={safeMetrics.eventsToday} icon={Activity} color="text-indigo-600" bg="bg-indigo-100" />
        <KPICard title="Potholes Detected" value={safeMetrics.potholesDetected} icon={MapPin} color="text-amber-600" bg="bg-amber-100" />
        <KPICard title="Critical Alerts" value={safeMetrics.criticalAlerts} icon={AlertTriangle} color="text-red-600" bg="bg-red-100" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Map Widget */}
        <div className="lg:col-span-2 bg-white rounded-lg shadow-xs border border-slate-200 p-4 min-h-[400px] flex flex-col">
          <h3 className="font-semibold text-lg mb-4 text-slate-800">City Map Overview</h3>
          <div className="flex-1 bg-slate-100 rounded border border-slate-200 overflow-hidden relative min-h-[320px]">
             <MiniMap events={recentEvents} />
          </div>
        </div>

        {/* System Alerts */}
        <div className="lg:col-span-1 h-[400px]">
          <AlertPanel
            alerts={alerts}
            onAcknowledge={(id) => {
              setAlerts((prev) => prev.map((a) => (a.id === id ? { ...a, acknowledged: true } : a)));
              setMetrics((prev) => (prev ? { ...prev, criticalAlerts: Math.max(0, prev.criticalAlerts - 1) } : prev));
            }}
          />
        </div>
      </div>

      {/* Future Scope Section */}
      <div className="mt-8 bg-gradient-to-r from-slate-900 to-slate-800 rounded-lg shadow-lg p-6 text-white">
        <div className="flex items-center gap-2 mb-4">
          <Sparkles className="w-6 h-6 text-amber-400" />
          <h3 className="text-xl font-bold">Future Capabilities (Roadmap)</h3>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white/10 p-4 rounded backdrop-blur-sm border border-white/5">
            <h4 className="font-semibold mb-1">Waterlogging</h4>
            <p className="text-xs text-slate-300">Detect flooded streets & blockages</p>
          </div>
          <div className="bg-white/10 p-4 rounded backdrop-blur-sm border border-white/5">
            <h4 className="font-semibold mb-1">Pedestrian Risk</h4>
            <p className="text-xs text-slate-300">Identify missing crossings & hazards</p>
          </div>
          <div className="bg-white/10 p-4 rounded backdrop-blur-sm border border-white/5">
            <h4 className="font-semibold mb-1">ANPR / Hit-and-Run</h4>
            <p className="text-xs text-slate-300">License plate recognition & tracking</p>
          </div>
          <div className="bg-white/10 p-4 rounded backdrop-blur-sm border border-white/5">
            <h4 className="font-semibold mb-1">Rash Driving</h4>
            <p className="text-xs text-slate-300">Analyze erratic vehicle behavior</p>
          </div>
        </div>
      </div>
    </div>
  );
}

function KPICard({ title, value, icon: Icon, color, bg }) {
  return (
    <div className="bg-white p-5 rounded-lg shadow-xs border border-slate-200 flex items-center gap-4">
      <div className={`p-3 rounded-full ${bg}`}>
        <Icon className={`w-6 h-6 ${color}`} />
      </div>
      <div>
        <p className="text-sm text-slate-500 font-medium">{title}</p>
        <p className="text-2xl font-bold text-slate-800">{value ?? '—'}</p>
      </div>
    </div>
  );
}
