import React, { useEffect, useState } from 'react';
import { getTrafficAnalytics, getTrafficSummary } from '../services/api';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, Legend, Cell, PieChart, Pie } from 'recharts';

export default function TrafficAnalytics() {
  const [data, setData] = useState(null);
  const [summary, setSummary] = useState(null);

  useEffect(() => {
    async function loadData() {
      try {
        const [analyticsData, summaryData] = await Promise.all([
          getTrafficAnalytics(),
          getTrafficSummary(),
        ]);
        setData(analyticsData);
        setSummary(summaryData);
      } catch (err) {
        console.error('Failed to load traffic analytics:', err);
      }
    }
    loadData();
  }, []);

  if (!data) return <div className="p-4">Loading analytics...</div>;

  const COLORS = ['#0ea5e9', '#f59e0b', '#10b981', '#6366f1'];

  const densityLabel =
    (summary?.avgTrafficDensity ?? 50) > 75
      ? 'Critical Delay'
      : (summary?.avgTrafficDensity ?? 50) > 50
      ? 'Moderate-Heavy'
      : 'Smooth Flow';

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-slate-800">Traffic Intelligence Analytics</h2>
      
      {/* Top Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-lg shadow border border-slate-200">
          <p className="text-sm text-slate-500 font-medium">Total Vehicles Detected</p>
          <p className="text-3xl font-bold text-slate-800 mt-1">
            {summary?.totalVehicles !== undefined ? summary.totalVehicles.toLocaleString() : '—'}
          </p>
          <p className="text-xs text-emerald-600 font-medium mt-1">Telemetry active across Delhi</p>
        </div>
        <div className="bg-white p-5 rounded-lg shadow border border-slate-200">
          <p className="text-sm text-slate-500 font-medium">Avg Traffic Density</p>
          <p className="text-3xl font-bold text-amber-600 mt-1">
            {summary?.avgTrafficDensity !== undefined ? `${summary.avgTrafficDensity}%` : '—'}
          </p>
          <p className="text-xs text-amber-700 font-medium mt-1">{densityLabel}</p>
        </div>
        <div className="bg-white p-5 rounded-lg shadow border border-slate-200">
          <p className="text-sm text-slate-500 font-medium">Congestion Hotspots</p>
          <p className="text-3xl font-bold text-slate-800 mt-1">
            {summary?.congestionHotspots ?? '—'}
          </p>
          <p className="text-xs text-rose-600 font-medium mt-1">
            {summary?.criticalHotspots ?? 0} high-severity clusters
          </p>
        </div>
        <div className="bg-white p-5 rounded-lg shadow border border-slate-200">
          <p className="text-sm text-slate-500 font-medium">Monitoring Fleet</p>
          <p className="text-3xl font-bold text-slate-800 mt-1">
            {summary?.monitoringFleet ?? '—'}
          </p>
          <p className="text-xs text-slate-500 font-medium mt-1">
            Active cameras: {summary?.activeCameras ?? 0}
          </p>
        </div>
      </div>


      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Density Over Time */}
        <div className="lg:col-span-2 bg-white p-5 rounded-lg shadow border border-slate-200">
          <h3 className="font-semibold text-lg mb-4 text-slate-800">Traffic Density Over Time</h3>
          <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data.densityOverTime}>
                <defs>
                  <linearGradient id="colorDensity" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#0ea5e9" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#0ea5e9" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                <XAxis dataKey="time" axisLine={false} tickLine={false} tick={{fill: '#64748b'}} />
                <YAxis axisLine={false} tickLine={false} tick={{fill: '#64748b'}} />
                <Tooltip 
                  contentStyle={{borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'}}
                />
                <Area type="monotone" dataKey="density" stroke="#0284c7" strokeWidth={3} fillOpacity={1} fill="url(#colorDensity)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Vehicle Types */}
        <div className="bg-white p-5 rounded-lg shadow border border-slate-200 flex flex-col">
          <h3 className="font-semibold text-lg mb-4 text-slate-800">Vehicle Classification</h3>
          <div className="flex-1 min-h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={data.vehicleTypes}
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {data.vehicleTypes.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend verticalAlign="bottom" height={36}/>
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Route Analytics */}
        <div className="lg:col-span-3 bg-white p-5 rounded-lg shadow border border-slate-200">
          <h3 className="font-semibold text-lg mb-4 text-slate-800">Live Route Congestion</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {data.routes.map(route => (
              <div key={route.id} className="p-4 rounded-lg border border-slate-100 bg-slate-50 flex flex-col gap-2">
                <div className="flex justify-between items-center">
                  <span className="font-bold text-slate-700">{route.id}</span>
                  <span className={`px-2 py-0.5 rounded text-xs font-bold ${
                    route.density === 'HIGH' ? 'bg-red-100 text-red-700' :
                    route.density === 'MEDIUM' ? 'bg-amber-100 text-amber-700' : 'bg-green-100 text-green-700'
                  }`}>
                    {route.density}
                  </span>
                </div>
                <div className="text-sm text-slate-500">
                  Avg Delay: <span className="font-semibold text-slate-800">{route.delay}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
