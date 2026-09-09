import React from 'react';
import { Loader2, AlertCircle, RefreshCw, Database } from 'lucide-react';
import { setForceDemoMode } from '../services/api';

// ─── Skeleton primitives ───────────────────────────────────────────────────

/** Animated pulsing placeholder block */
function SkeletonBlock({ className = '' }) {
  return <div className={`animate-pulse rounded bg-slate-200 ${className}`} />;
}

/**
 * Skeleton for a single KPI stat card (icon circle + two text lines).
 * Matches the real KPICard layout used in Overview.
 */
export function SkeletonCard() {
  return (
    <div className="bg-white p-5 rounded-lg shadow-xs border border-slate-200 flex items-center gap-4">
      <SkeletonBlock className="w-12 h-12 rounded-full shrink-0" />
      <div className="flex-1 space-y-2">
        <SkeletonBlock className="h-3 w-24" />
        <SkeletonBlock className="h-7 w-16" />
        <SkeletonBlock className="h-2.5 w-32" />
      </div>
    </div>
  );
}

/**
 * Skeleton for a map/chart panel.
 */
export function SkeletonMap({ height = 'h-80' }) {
  return (
    <div className={`bg-white rounded-lg shadow-xs border border-slate-200 p-4 flex flex-col gap-3`}>
      <div className="flex justify-between items-center">
        <SkeletonBlock className="h-5 w-36" />
        <SkeletonBlock className="h-5 w-20 rounded-full" />
      </div>
      <SkeletonBlock className={`${height} rounded`} />
    </div>
  );
}

/**
 * Skeleton for a data table (header + rows).
 */
export function SkeletonTable({ rows = 5 }) {
  return (
    <div className="bg-white rounded-lg shadow-xs border border-slate-200 overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-slate-200 bg-slate-50 flex gap-4">
        {[40, 24, 20, 16].map((w, i) => (
          <SkeletonBlock key={i} className={`h-4 w-${w}`} />
        ))}
      </div>
      {/* Rows */}
      <div className="divide-y divide-slate-100">
        {[...Array(rows)].map((_, i) => (
          <div key={i} className="px-4 py-3 flex gap-4 items-center">
            <SkeletonBlock className="h-3.5 w-40 shrink-0" />
            <SkeletonBlock className="h-3.5 w-24" />
            <SkeletonBlock className="h-3.5 w-20" />
            <SkeletonBlock className="h-5 w-16 rounded-full ml-auto" />
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * Full-page skeleton for the Overview dashboard (KPI grid + map + alert panel).
 */
export function SkeletonOverview() {
  return (
    <div className="space-y-6">
      {/* Title row */}
      <div className="flex justify-between items-center">
        <div className="space-y-2">
          <SkeletonBlock className="h-7 w-48" />
          <SkeletonBlock className="h-3.5 w-72" />
        </div>
        <SkeletonBlock className="h-7 w-36 rounded-full" />
      </div>
      {/* KPI cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => <SkeletonCard key={i} />)}
      </div>
      {/* Map + alerts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <SkeletonMap height="h-80" />
        </div>
        <div className="space-y-3">
          <SkeletonBlock className="h-64 rounded-lg" />
        </div>
      </div>
    </div>
  );
}

// ─── Status States ─────────────────────────────────────────────────────────

export function LoadingState({ message = 'Loading urban intelligence data...' }) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[350px] p-8 text-center bg-white rounded-lg border border-slate-200 shadow-xs">
      <Loader2 className="w-8 h-8 text-brand-600 animate-spin mb-3" />
      <p className="text-sm font-medium text-slate-700">{message}</p>
      <p className="text-xs text-slate-400 mt-1">Connecting to Urban Intelligence stream...</p>
    </div>
  );
}

export function ErrorState({
  title = 'Unable to Load Data',
  message = 'A connection to the urban intelligence service could not be established.',
  onRetry,
}) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[350px] p-8 text-center bg-white rounded-lg border border-rose-200 shadow-xs">
      <div className="p-3 bg-rose-100 rounded-full text-rose-600 mb-3">
        <AlertCircle className="w-8 h-8" />
      </div>
      <h3 className="text-base font-bold text-slate-800 mb-1">{title}</h3>
      <p className="text-sm text-slate-600 max-w-md mb-5">{message}</p>
      <div className="flex flex-wrap items-center justify-center gap-3">
        {onRetry && (
          <button
            onClick={onRetry}
            className="flex items-center gap-1.5 px-4 py-2 bg-slate-900 text-white rounded-md text-sm font-medium hover:bg-slate-800 transition cursor-pointer"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Retry Connection</span>
          </button>
        )}
        <button
          onClick={() => { setForceDemoMode(true); if (onRetry) onRetry(); }}
          className="flex items-center gap-1.5 px-4 py-2 bg-brand-50 border border-brand-300 text-brand-700 rounded-md text-sm font-medium hover:bg-brand-100 transition cursor-pointer"
        >
          <Database className="w-4 h-4" />
          <span>Use Demo Data</span>
        </button>
      </div>
    </div>
  );
}
