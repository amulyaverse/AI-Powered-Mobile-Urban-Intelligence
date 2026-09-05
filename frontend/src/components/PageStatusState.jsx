import React from 'react';
import { Loader2, AlertCircle, RefreshCw, Database } from 'lucide-react';
import { setForceDemoMode } from '../services/api';

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
          onClick={() => {
            setForceDemoMode(true);
            if (onRetry) onRetry();
          }}
          className="flex items-center gap-1.5 px-4 py-2 bg-brand-50 border border-brand-300 text-brand-700 rounded-md text-sm font-medium hover:bg-brand-100 transition cursor-pointer"
        >
          <Database className="w-4 h-4" />
          <span>Use Demo Data</span>
        </button>
      </div>
    </div>
  );
}
