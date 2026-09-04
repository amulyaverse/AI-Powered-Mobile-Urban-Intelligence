import React, { useEffect, useState } from 'react';
import { getKPIMetrics, getEvents, getSystemAlerts } from '../services/api';
import { Activity, AlertTriangle, MapPin, Truck, Sparkles } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import AlertPanel from '../components/AlertPanel';
import MiniMap from '../components/MiniMap';

export default function Overview() {
  const [metrics, setMetrics] = useState(null);
  const [recentEvents, setRecentEvents] = useState([]);
  const [alerts, setAlerts] = useState([]);

  useEffect(() => {
    async function loadData() {
      const [m, e, a] = await Promise.all([
        getKPIMetrics(),
        getEvents(),
        getSystemAlerts(),
      ]);
      setMetrics(m);
      setRecentEvents(e);
      setAlerts(a);
    }
    loadData();
    // Poll every 10 seconds for live updates
    const interval = setInterval(loadData, 10_000);
    return () => clearInterval(interval);
  }, []);

  if (!metrics) return <div className="p-4">Loading data...</div>;

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-slate-800">Platform Overview</h2>
      
      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard title="Active Buses" value={metrics.activeBuses} icon={Truck} color="text-blue-600" bg="bg-blue-100" />
        <KPICard title="Events Today" value={metrics.eventsToday} icon={Activity} color="text-indigo-600" bg="bg-indigo-100" />
        <KPICard title="Potholes Detected" value={metrics.potholesDetected} icon={MapPin} color="text-amber-600" bg="bg-amber-100" />
        <KPICard title="Critical Alerts" value={metrics.criticalAlerts} icon={AlertTriangle} color="text-red-600" bg="bg-red-100" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Map Widget */}
        <div className="lg:col-span-2 bg-white rounded-lg shadow border border-slate-200 p-4 min-h-[400px] flex flex-col">
          <h3 className="font-semibold text-lg mb-4">City Map Overview</h3>
          <div className="flex-1 bg-slate-100 rounded border border-slate-200 overflow-hidden relative">
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
          <Sparkles className="w-6 h-6 text-brand-400" />
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
    <div className="bg-white p-5 rounded-lg shadow border border-slate-200 flex items-center gap-4">
      <div className={`p-3 rounded-full ${bg}`}>
        <Icon className={`w-6 h-6 ${color}`} />
      </div>
      <div>
        <p className="text-sm text-slate-500 font-medium">{title}</p>
        <p className="text-2xl font-bold text-slate-800">{value}</p>
      </div>
    </div>
  );
}
