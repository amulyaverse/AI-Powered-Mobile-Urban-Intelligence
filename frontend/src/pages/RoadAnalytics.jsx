import React, { useEffect, useState } from 'react';
import { getRoadConditionAnalytics, getRoadSummary } from '../services/api';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, LineChart, Line } from 'recharts';

export default function RoadAnalytics() {
  const [data, setData] = useState(null);
  const [summary, setSummary] = useState(null);

  useEffect(() => {
    async function loadData() {
      try {
        const [analyticsData, summaryData] = await Promise.all([
          getRoadConditionAnalytics(),
          getRoadSummary(),
        ]);
        setData(analyticsData);
        setSummary(summaryData);
      } catch (err) {
        console.error('Failed to load road analytics:', err);
      }
    }
    loadData();
  }, []);

  if (!data) return <div className="p-4">Loading analytics...</div>;

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-slate-800">Road Condition Analytics</h2>
      
      {/* Top Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-lg shadow border border-slate-200">
          <p className="text-sm text-slate-500 font-medium">Total Potholes Detected</p>
          <p className="text-3xl font-bold text-slate-800 mt-1">
            {summary?.totalPotholes !== undefined ? summary.totalPotholes.toLocaleString() : '—'}
          </p>
          <p className="text-xs text-slate-500 mt-1">Verified fleet observations</p>
        </div>
        <div className="bg-white p-5 rounded-lg shadow border-slate-200 border-l-4 border-l-red-500">
          <p className="text-sm text-slate-500 font-medium">High Severity Issues</p>
          <p className="text-3xl font-bold text-slate-800 mt-1">
            {summary?.highSeverityIssues ?? '—'}
          </p>
          <p className="text-xs text-rose-600 font-medium mt-1">Require immediate maintenance</p>
        </div>
        <div className="bg-white p-5 rounded-lg shadow border border-slate-200">
          <p className="text-sm text-slate-500 font-medium">Persistent Defects</p>
          <p className="text-3xl font-bold text-slate-800 mt-1">
            {summary?.persistentDefects ?? '—'}
          </p>
          <p className="text-xs text-amber-600 font-medium mt-1">Clustered hotspot locations</p>
        </div>
        <div className="bg-white p-5 rounded-lg shadow border border-slate-200">
          <p className="text-sm text-slate-500 font-medium">Resolved Defects</p>
          <p className="text-3xl font-bold text-emerald-600 mt-1">
            {summary?.resolvedDefects ?? '—'}
          </p>
          <p className="text-xs text-emerald-700 font-medium mt-1">Closed action items</p>
        </div>
      </div>


      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Severity Distribution */}
        <div className="bg-white p-5 rounded-lg shadow border border-slate-200">
          <h3 className="font-semibold text-lg mb-4 text-slate-800">Defect Severity Distribution</h3>
          <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.severityDistribution}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{fill: '#64748b'}} />
                <YAxis axisLine={false} tickLine={false} tick={{fill: '#64748b'}} />
                <Tooltip 
                  cursor={{fill: '#f8fafc'}}
                  contentStyle={{borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'}}
                />
                <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                  {data.severityDistribution.map((entry, index) => (
                    <cell key={`cell-${index}`} fill={
                      entry.name.includes('High') ? '#ef4444' : 
                      entry.name.includes('Medium') ? '#f59e0b' : '#10b981'
                    } />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Defects Over Time */}
        <div className="bg-white p-5 rounded-lg shadow border border-slate-200">
          <h3 className="font-semibold text-lg mb-4 text-slate-800">Defect Reporting Trends</h3>
          <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data.defectsOverTime}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                <XAxis dataKey="day" axisLine={false} tickLine={false} tick={{fill: '#64748b'}} />
                <YAxis axisLine={false} tickLine={false} tick={{fill: '#64748b'}} />
                <Tooltip 
                  contentStyle={{borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'}}
                />
                <Legend />
                <Line type="monotone" dataKey="newDefects" name="New Defects Detected" stroke="#ef4444" strokeWidth={3} dot={{r: 4}} activeDot={{r: 6}} />
                <Line type="monotone" dataKey="resolved" name="Defects Resolved" stroke="#10b981" strokeWidth={3} dot={{r: 4}} activeDot={{r: 6}} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
