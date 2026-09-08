import React, { useEffect, useState, useCallback } from 'react';
import { getKPIMetrics, getEvents, getSystemAlerts } from '../services/api';
import { useEventWebSocket } from '../hooks/useEventWebSocket';
import { Activity, AlertTriangle, MapPin, Truck, Sparkles, Wifi, Radio } from 'lucide-react';
import AlertPanel from '../components/AlertPanel';
import MiniMap from '../components/MiniMap';
import { LoadingState, ErrorState } from '../components/PageStatusState';

export default function Overview() {
  const [metrics, setMetrics] = useState(null);
  const [recentEvents, setRecentEvents] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Live WebSocket event subscription
  const { latestEvent, isConnected: isWsConnected } = useEventWebSocket();

  const loadData = useCallback(async (isInitial = false) => {
    if (isInitial) setLoading(true);
    try {
      const [m, e, a] = await Promise.all([
        getKPIMetrics(),
        getEvents({ limit: 30 }),
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
    // Poll every 10 seconds for background sync
    const interval = setInterval(() => loadData(false), 10_000);
    return () => clearInterval(interval);
  }, [loadData]);

  // Dynamically assimilate incoming live edge detections & update metrics in real time
  useEffect(() => {
    if (!latestEvent?.event_id) return;

    // 1. Prepend incoming real incident to recentEvents (for MiniMap & live radar)
    setRecentEvents((prev) => {
      const filtered = prev.filter((e) => (e.event_id || e.id) !== latestEvent.event_id);
      return [latestEvent, ...filtered].slice(0, 40);
    });

    // 2. Increment real-time counters dynamically
    setMetrics((prev) => {
      if (!prev) return prev;
      const eventType = (latestEvent.event_type || '').toLowerCase();
      const isPothole = eventType.includes('pothole') || eventType.includes('defect') || eventType.includes('crack');
      const isCritical = (latestEvent.severity || '').toLowerCase() === 'critical';

      return {
        ...prev,
        eventsToday: (prev.eventsToday || 0) + 1,
        total_events: (prev.total_events || prev.eventsToday || 0) + 1,
        potholesDetected: isPothole ? (prev.potholesDetected || 0) + 1 : (prev.potholesDetected || 0),
        criticalAlerts: isCritical ? (prev.criticalAlerts || 0) + 1 : (prev.criticalAlerts || 0),
      };
    });

    // 3. If critical or high severity incident, also push an alert notification
    const sev = (latestEvent.severity || '').toLowerCase();
    if (sev === 'critical' || sev === 'high') {
      const alertId = `ALT_${latestEvent.event_id}`;
      const newAlert = {
        id: alertId,
        severity: sev,
        message: `${(latestEvent.event_type || 'Defect').toUpperCase()} detected by ${latestEvent.bus_id || 'Fleet'}`,
        source: latestEvent.bus_id || 'Bus Camera',
        details: latestEvent.latitude && latestEvent.longitude
          ? `Lat: ${Number(latestEvent.latitude).toFixed(4)}, Lng: ${Number(latestEvent.longitude).toFixed(4)}`
          : 'Transit corridor anomaly',
        timestamp: latestEvent.timestamp || new Date().toISOString(),
        acknowledged: false,
      };

      setAlerts((prev) => {
        if (prev.some((a) => a.id === alertId)) return prev;
        return [newAlert, ...prev].slice(0, 25);
      });
    }
  }, [latestEvent]);

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
    activeBuses: 6,
    eventsToday: 99,
    potholesDetected: 64,
    criticalAlerts: 1,
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-slate-800">Platform Overview</h2>
          <p className="text-xs text-slate-500">
            Real-time mobile sensing and intelligence aggregated across active fleet
          </p>
        </div>

        {/* Live sync indicator */}
        <div className="flex items-center gap-2">
          {isWsConnected ? (
            <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <Wifi className="w-3.5 h-3.5" />
              Live Ingestion Active
            </span>
          ) : (
            <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-slate-100 text-slate-600 border border-slate-200">
              <Radio className="w-3.5 h-3.5 text-slate-400" />
              Synchronized Telemetry
            </span>
          )}
        </div>
      </div>

      {/* KPI Cards — Powered by Real Incident Aggregates */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          title="Active Buses"
          value={`${safeMetrics.activeBuses} Units`}
          subtext="Reporting to centralized GIS"
          icon={Truck}
          color="text-blue-600"
          bg="bg-blue-100"
        />
        <KPICard
          title="Events Today"
          value={safeMetrics.eventsToday}
          subtext="Verified mobile edge detections"
          icon={Activity}
          color="text-indigo-600"
          bg="bg-indigo-100"
        />
        <KPICard
          title="Potholes Detected"
          value={safeMetrics.potholesDetected}
          subtext="Road defects & surface cracks"
          icon={MapPin}
          color="text-amber-600"
          bg="bg-amber-100"
        />
        <KPICard
          title="Critical Alerts"
          value={safeMetrics.criticalAlerts}
          subtext="Pending municipal action"
          icon={AlertTriangle}
          color="text-red-600"
          bg="bg-red-100"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Map Widget with interactive incident popups */}
        <div className="lg:col-span-2 bg-white rounded-lg shadow-xs border border-slate-200 p-4 min-h-[420px] flex flex-col">
          <div className="flex justify-between items-center mb-3">
            <div>
              <h3 className="font-semibold text-lg text-slate-800">City Map Overview</h3>
              <p className="text-xs text-slate-500">
                Click any incident marker to preview detected defect evidence & location
              </p>
            </div>
            <span className="text-xs bg-slate-100 text-slate-700 px-2.5 py-1 rounded font-mono font-medium">
              {recentEvents.length} Recent Detections
            </span>
          </div>
          <div className="flex-1 bg-slate-100 rounded border border-slate-200 overflow-hidden relative min-h-[340px]">
            <MiniMap events={recentEvents} />
          </div>
        </div>

        {/* System Alerts */}
        <div className="lg:col-span-1 h-[420px]">
          <AlertPanel
            alerts={alerts}
            onAcknowledge={(id) => {
              setAlerts((prev) => prev.map((a) => (a.id === id ? { ...a, acknowledged: true } : a)));
              setMetrics((prev) => (prev ? { ...prev, criticalAlerts: Math.max(0, prev.criticalAlerts - 1) } : prev));
            }}
          />
        </div>
      </div>

      {/* Future Scope Section — Kept as requested by user */}
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

function KPICard({ title, value, subtext, icon: Icon, color, bg }) {
  return (
    <div className="bg-white p-5 rounded-lg shadow-xs border border-slate-200 flex items-center gap-4">
      <div className={`p-3 rounded-full ${bg} shrink-0`}>
        <Icon className={`w-6 h-6 ${color}`} />
      </div>
      <div className="min-w-0">
        <p className="text-xs text-slate-500 font-medium">{title}</p>
        <p className="text-2xl font-bold text-slate-800 mt-0.5">{value ?? '—'}</p>
        {subtext && <p className="text-[11px] text-slate-400 truncate mt-0.5">{subtext}</p>}
      </div>
    </div>
  );
}
