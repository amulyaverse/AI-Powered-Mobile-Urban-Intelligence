import React, { useEffect, useState, useCallback } from 'react';
import { getRoadConditionAnalytics, getRoadSummary } from '../services/api';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, LineChart, Line, Cell } from 'recharts';
import { LoadingState, ErrorState } from '../components/PageStatusState';

export default function RoadAnalytics() {
  const [data, setData] = useState(null);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadData = useCallback(async (isInitial = false) => {
    if (isInitial) setLoading(true);
    try {
      const [analyticsData, summaryData] = await Promise.all([
        getRoadConditionAnalytics(),
        getRoadSummary(),
      ]);
      setData(analyticsData);
      setSummary(summaryData);
      setError(null);
    } catch (err) {
      console.error('[RoadAnalytics] Failed to load road analytics:', err);
      setError(err.message || 'Failed to load road analytics.');
    } finally {
      if (isInitial) setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData(true);
  }, [loadData]);

  if (loading && !data) {
    return <LoadingState message="Loading road defect analytics and severity models..." />;
  }

  if (error && !data) {
    return (
      <ErrorState
        title="Road Analytics Unavailable"
        message="Could not load road condition charts. You can retry the connection or switch to Demo Mode."
        onRetry={() => loadData(true)}
      />
    );
  }

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-slate-800">Road Condition Analytics</h2>
      
      {/* Top Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-lg shadow-xs border border-slate-200">
          <p className="text-sm text-slate-500 font-medium">Total Potholes Detected</p>
          <p className="text-3xl font-bold text-slate-800 mt-1">
            {summary?.totalPotholes !== undefined ? summary.totalPotholes.toLocaleString() : '—'}
          </p>
          <p className="text-xs text-slate-500 mt-1">Verified fleet observations</p>
        </div>
        <div className="bg-white p-5 rounded-lg shadow-xs border-slate-200 border-l-4 border-l-red-500">
          <p className="text-sm text-slate-500 font-medium">High Severity Issues</p>
          <p className="text-3xl font-bold text-slate-800 mt-1">
            {summary?.highSeverityIssues ?? '—'}
          </p>
          <p className="text-xs text-rose-600 font-medium mt-1">Require immediate maintenance</p>
        </div>
        <div className="bg-white p-5 rounded-lg shadow-xs border border-slate-200">
          <p className="text-sm text-slate-500 font-medium">Persistent Defects</p>
          <p className="text-3xl font-bold text-slate-800 mt-1">
            {summary?.persistentDefects ?? '—'}
          </p>
          <p className="text-xs text-amber-600 font-medium mt-1">Clustered hotspot locations</p>
        </div>
        <div className="bg-white p-5 rounded-lg shadow-xs border border-slate-200">
          <p className="text-sm text-slate-500 font-medium">Resolved Defects</p>
          <p className="text-3xl font-bold text-emerald-600 mt-1">
            {summary?.resolvedDefects ?? '—'}
          </p>
          <p className="text-xs text-emerald-700 font-medium mt-1">Closed action items</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Severity Distribution */}
        <div className="bg-white p-5 rounded-lg shadow-xs border border-slate-200">
          <h3 className="font-semibold text-lg mb-4 text-slate-800">Defect Severity Distribution</h3>
          <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data?.severityDistribution || []}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{fill: '#64748b'}} />
                <YAxis axisLine={false} tickLine={false} tick={{fill: '#64748b'}} />
                <Tooltip 
                  cursor={{fill: '#f8fafc'}}
                  contentStyle={{borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'}}
                />
                <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                  {(data?.severityDistribution || []).map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={
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
        <div className="bg-white p-5 rounded-lg shadow-xs border border-slate-200">
          <h3 className="font-semibold text-lg mb-4 text-slate-800">Defect Reporting Trends</h3>
          <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data?.defectsOverTime || []}>
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

      {/* PR #37 Edge AI Architecture & Model Card */}
      <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 rounded-xl p-6 text-white shadow-md border border-slate-700">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border-b border-slate-700/80 pb-4 mb-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="bg-amber-500 text-slate-950 font-extrabold text-[11px] px-2.5 py-0.5 rounded-full uppercase tracking-wider">
                PR #37 Edge AI Module
              </span>
              <span className="text-slate-400 text-xs font-mono">Pothole_Road_Condition_Model</span>
            </div>
            <h3 className="text-lg font-bold text-slate-100">
              YOLOv8 Real-Time Pothole & Road Damage Detection Pipeline
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Indian road defect computer vision model trained on Roboflow v5 dataset with dual severity heuristics.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <span className="px-3 py-1 bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 rounded-full text-xs font-semibold">
              Verified Pipeline ✅
            </span>
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white/5 border border-white/10 rounded-lg p-3.5">
            <p className="text-[11px] text-slate-400 font-medium">Precision</p>
            <p className="text-2xl font-bold text-amber-400 mt-1">84.2%</p>
            <p className="text-[10px] text-slate-400 mt-0.5">Test split validation</p>
          </div>
          <div className="bg-white/5 border border-white/10 rounded-lg p-3.5">
            <p className="text-[11px] text-slate-400 font-medium">Recall Rate</p>
            <p className="text-2xl font-bold text-amber-400 mt-1">78.9%</p>
            <p className="text-[10px] text-slate-400 mt-0.5">Surface defect hit rate</p>
          </div>
          <div className="bg-white/5 border border-white/10 rounded-lg p-3.5">
            <p className="text-[11px] text-slate-400 font-medium">mAP @ 50</p>
            <p className="text-2xl font-bold text-emerald-400 mt-1">81.6%</p>
            <p className="text-[10px] text-slate-400 mt-0.5">YOLOv8 Nano backbone</p>
          </div>
          <div className="bg-white/5 border border-white/10 rounded-lg p-3.5">
            <p className="text-[11px] text-slate-400 font-medium">Active Heuristic</p>
            <p className="text-sm font-bold text-blue-300 mt-2">Approach A & B</p>
            <p className="text-[10px] text-slate-400 mt-0.5">Width & Depth Scaling</p>
          </div>
        </div>
      </div>
    </div>
  );
}
