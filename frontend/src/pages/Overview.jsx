import React, { useEffect, useState, useCallback } from 'react';
import { getKPIMetrics, getEvents, getSystemAlerts } from '../services/api';
import { useEventWebSocket } from '../hooks/useEventWebSocket';
import { Activity, AlertTriangle, MapPin, Truck, Sparkles, Wifi, Radio, TrendingUp, TrendingDown } from 'lucide-react';
import AlertPanel from '../components/AlertPanel';
import MiniMap from '../components/MiniMap';
import KPISparkline from '../components/KPISparkline';
import { LoadingState, ErrorState } from '../components/PageStatusState';

export default function Overview() {
  const [metrics, setMetrics]           = useState(null);
  const [recentEvents, setRecentEvents] = useState([]);
  const [alerts, setAlerts]             = useState([]);
  const [selectedEventId, setSelectedEventId] = useState(null);
  const [loading, setLoading]           = useState(true);
  const [error, setError]               = useState(null);

  const { latestEvent, isConnected: isWsConnected } = useEventWebSocket();

  const loadData = useCallback(async (isInitial = false) => {
    if (isInitial) setLoading(true);
    try {
      const [m, e, a] = await Promise.all([
        getKPIMetrics(),
        getEvents({ limit: 40 }),
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
    const interval = setInterval(() => loadData(false), 10_000);
    return () => clearInterval(interval);
  }, [loadData]);

  useEffect(() => {
    if (!latestEvent?.event_id) return;
    setRecentEvents((prev) => {
      const filtered = prev.filter((e) => (e.event_id || e.id) !== latestEvent.event_id);
      return [latestEvent, ...filtered].slice(0, 50);
    });
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

  if (loading && !metrics) return <LoadingState message="Loading urban intelligence overview..." />;
  if (error && !metrics) return (
    <ErrorState
      title="Command Center Unavailable"
      message="Could not load platform metrics. You can retry the connection or switch to Demo Mode."
      onRetry={() => loadData(true)}
    />
  );

  const safeMetrics = metrics || { activeBuses: 6, eventsToday: 99, potholesDetected: 64, criticalAlerts: 1 };

  return (
    <div className="space-y-6">

      {/* ── Page Header ───────────────────────────────────────── */}
      <div className="flex justify-between items-start">
        <div>
          <h2 className="text-2xl font-extrabold text-slate-800 tracking-tight">Platform Overview</h2>
          <p className="text-sm text-gis-slate mt-0.5">
            Real-time mobile sensing aggregated across active fleet
          </p>
        </div>
        <div className="flex items-center gap-2 mt-1">
          {isWsConnected ? (
            <span className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-bold bg-gis-sage-light text-gis-sage-dark border border-gis-sage/25 shadow-sm">
              <span className="w-1.5 h-1.5 rounded-full bg-gis-sage animate-pulse" />
              <Wifi className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Live Ingestion</span>
            </span>
          ) : (
            <span className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-bold bg-gis-slate-light text-gis-slate border border-gis-slate/20">
              <Radio className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Synchronized</span>
            </span>
          )}
        </div>
      </div>

      {/* ── KPI Cards ─────────────────────────────────────────── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          title="Active Buses"
          value={`${safeMetrics.activeBuses}`}
          unit="units"
          subtext="Reporting to centralized GIS"
          icon={Truck}
          accentColor="#5b7fa6"
          trend={+2}
          sparkColor="#5b7fa6"
        />
        <KPICard
          title="Events Today"
          value={safeMetrics.eventsToday}
          subtext="Verified mobile edge detections"
          icon={Activity}
          accentColor="#7a9e7e"
          trend={+12}
          sparkColor="#7a9e7e"
        />
        <KPICard
          title="Potholes Detected"
          value={safeMetrics.potholesDetected}
          subtext="Road defects & surface cracks"
          icon={MapPin}
          accentColor="#a08c5a"
          trend={-3}
          sparkColor="#a08c5a"
        />
        <KPICard
          title="Critical Alerts"
          value={safeMetrics.criticalAlerts}
          subtext="Pending municipal action"
          icon={AlertTriangle}
          accentColor="#9b7a84"
          trend={0}
          sparkColor="#9b7a84"
        />
      </div>

      {/* ── Map + Alerts ──────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Map Widget */}
        <div className="lg:col-span-2 bg-white rounded-3xl shadow-card border border-gis-border p-5 min-h-[440px] flex flex-col card-enter">
          <div className="flex justify-between items-start mb-4">
            <div>
              <h3 className="font-extrabold text-base text-slate-800">City Map Overview</h3>
              <p className="text-xs text-gis-slate mt-0.5">
                OpenStreetMap GIS layer · Click any marker or alert to inspect incident details
              </p>
            </div>
            <div className="flex items-center gap-2">
              {selectedEventId && (
                <button
                  onClick={() => setSelectedEventId(null)}
                  className="text-xs text-slate-500 hover:text-slate-700 bg-slate-100 px-2.5 py-1 rounded-full font-bold transition-colors cursor-pointer"
                >
                  Clear Selection
                </button>
              )}
              <span className="text-xs bg-gis-slate-light text-gis-slate-dark px-3 py-1.5 rounded-full font-bold border border-gis-border">
                {recentEvents.length} Detections
              </span>
            </div>
          </div>
          <div className="flex-1 rounded-2xl overflow-hidden relative min-h-[340px] border border-gis-border/60">
            <MiniMap
              events={recentEvents}
              selectedEventId={selectedEventId}
              onSelectEvent={setSelectedEventId}
            />
          </div>
        </div>

        {/* Alerts */}
        <div className="lg:col-span-1 h-[440px] card-enter">
          <AlertPanel
            alerts={alerts}
            selectedEventId={selectedEventId}
            onSelectEvent={setSelectedEventId}
            onAcknowledge={(id) => {
              setAlerts((prev) => prev.map((a) => (a.id === id ? { ...a, acknowledged: true } : a)));
              setMetrics((prev) => (prev ? { ...prev, criticalAlerts: Math.max(0, prev.criticalAlerts - 1) } : prev));
            }}
          />
        </div>
      </div>

      {/* ── Roadmap Section ──────────────────────────────────── */}
      <div className="bg-gradient-to-br from-gis-slate-dark to-gis-blue-dark rounded-3xl shadow-card p-6 text-white card-enter">
        <div className="flex items-center gap-2.5 mb-5">
          <div className="w-8 h-8 rounded-2xl bg-white/15 flex items-center justify-center">
            <Sparkles className="w-4.5 h-4.5 text-amber-300" />
          </div>
          <h3 className="text-lg font-extrabold tracking-tight">Future Capabilities</h3>
          <span className="ml-auto text-[10px] font-bold px-2.5 py-1 bg-white/15 rounded-full text-white/80 uppercase tracking-wide">Roadmap</span>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[
            { title: 'Waterlogging', desc: 'Detect flooded streets & blockages' },
            { title: 'Pedestrian Risk', desc: 'Identify missing crossings & hazards' },
            { title: 'ANPR / Hit-and-Run', desc: 'License plate recognition & tracking' },
            { title: 'Rash Driving', desc: 'Analyze erratic vehicle behavior' },
          ].map(({ title, desc }) => (
            <div
              key={title}
              className="bg-white/10 hover:bg-white/15 p-4 rounded-2xl border border-white/10 transition-all duration-200 hover:scale-[1.02] cursor-default"
            >
              <h4 className="font-bold text-sm mb-1 text-white">{title}</h4>
              <p className="text-xs text-white/60 leading-relaxed">{desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ── KPI Card Component ─────────────────────────────────────────── */
function KPICard({ title, value, unit, subtext, icon: Icon, accentColor, trend, sparkColor }) {
  const isUp   = trend > 0;
  const isDown = trend < 0;
  const trendLabel = trend === 0 ? 'Stable' : `${isUp ? '+' : ''}${trend} today`;

  return (
    <div
      className="bg-white rounded-3xl shadow-card border border-gis-border p-5 flex flex-col gap-3
                 hover:shadow-card-hover hover:scale-[1.02] transition-all duration-200 cursor-default card-enter"
    >
      {/* Top row */}
      <div className="flex items-start justify-between">
        <div
          className="w-10 h-10 rounded-2xl flex items-center justify-center shrink-0"
          style={{ backgroundColor: `${accentColor}18` }}
        >
          <Icon className="w-5 h-5" style={{ color: accentColor }} />
        </div>
        <div
          className="flex items-center gap-1 px-2.5 py-1 rounded-full text-[10px] font-bold"
          style={{
            backgroundColor: isUp ? '#7a9e7e18' : isDown ? '#9b7a8418' : '#7c8fa618',
            color: isUp ? '#4e7052' : isDown ? '#7a4e5c' : '#5a6e82',
          }}
        >
          {isUp   && <TrendingUp   className="w-3 h-3" />}
          {isDown && <TrendingDown className="w-3 h-3" />}
          {trendLabel}
        </div>
      </div>

      {/* Value */}
      <div>
        <p className="text-xs text-gis-slate font-semibold tracking-wide uppercase">{title}</p>
        <div className="flex items-baseline gap-1 mt-0.5">
          <p className="text-3xl font-extrabold text-slate-800 leading-none">{value ?? '—'}</p>
          {unit && <span className="text-sm text-gis-slate font-semibold">{unit}</span>}
        </div>
        {subtext && <p className="text-[11px] text-gis-slate/80 mt-1 truncate">{subtext}</p>}
      </div>

      {/* Sparkline */}
      <div className="-mx-1">
        <KPISparkline value={value} color={sparkColor} />
      </div>
    </div>
  );
}
