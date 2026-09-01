import React from 'react';
import { formatDistanceToNow } from 'date-fns';
import { AlertCircle, AlertTriangle, Info } from 'lucide-react';

export default function AlertPanel({ alerts }) {
  const getAlertStyles = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'critical':
        return {
          bg: 'bg-red-50',
          border: 'border-red-200',
          icon: <AlertCircle className="w-5 h-5 text-red-600" />,
          text: 'text-red-800',
          tag: 'bg-red-100 text-red-700'
        };
      case 'high':
        return {
          bg: 'bg-amber-50',
          border: 'border-amber-200',
          icon: <AlertTriangle className="w-5 h-5 text-amber-600" />,
          text: 'text-amber-800',
          tag: 'bg-amber-100 text-amber-700'
        };
      default:
        return {
          bg: 'bg-blue-50',
          border: 'border-blue-200',
          icon: <Info className="w-5 h-5 text-blue-600" />,
          text: 'text-blue-800',
          tag: 'bg-blue-100 text-blue-700'
        };
    }
  };

  if (!alerts || alerts.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow border border-slate-200 p-6 text-center text-slate-500">
        No active alerts at this time.
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow border border-slate-200 overflow-hidden flex flex-col h-full">
      <div className="p-4 border-b border-slate-200 bg-slate-50 flex justify-between items-center">
        <h3 className="font-semibold text-lg text-slate-800">System Alerts</h3>
        <span className="bg-red-100 text-red-700 py-0.5 px-2 rounded-full text-xs font-bold">
          {alerts.filter(a => a.severity === 'critical' || a.severity === 'high').length} Critical
        </span>
      </div>
      <div className="p-4 space-y-3 overflow-y-auto flex-1">
        {alerts.map((alert) => {
          const styles = getAlertStyles(alert.severity);
          return (
            <div key={alert.id} className={`p-3 rounded-md border ${styles.bg} ${styles.border} flex gap-3`}>
              <div className="mt-0.5">{styles.icon}</div>
              <div className="flex-1">
                <div className="flex justify-between items-start mb-1">
                  <span className={`text-xs font-bold uppercase tracking-wider px-2 py-0.5 rounded ${styles.tag}`}>
                    {alert.severity}
                  </span>
                  <span className="text-xs text-slate-500">
                    {formatDistanceToNow(new Date(alert.timestamp))} ago
                  </span>
                </div>
                <p className={`font-semibold text-sm mb-1 ${styles.text}`}>{alert.message}</p>
                <p className="text-xs text-slate-600 flex items-center gap-2">
                  <span className="font-medium text-slate-700">{alert.source}</span>
                  {alert.details && <span>• {alert.details}</span>}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
