import React, { useState } from 'react';
import { formatDistanceToNow } from 'date-fns';
import { AlertCircle, AlertTriangle, Info, Check, CheckCheck } from 'lucide-react';
import { acknowledgeAlert } from '../services/api';

export default function AlertPanel({ alerts: initialAlerts = [], onAcknowledge }) {
  const [alerts, setAlerts] = useState(initialAlerts);
  const [acknowledgingId, setAcknowledgingId] = useState(null);

  // Sync with prop when parent updates
  React.useEffect(() => {
    setAlerts(initialAlerts);
  }, [initialAlerts]);

  const handleAcknowledge = async (id) => {
    setAcknowledgingId(id);
    try {
      const updated = await acknowledgeAlert(id);
      setAlerts((prev) => prev.map((a) => (a.id === id ? { ...a, acknowledged: true } : a)));
      if (onAcknowledge) onAcknowledge(id);
    } catch (err) {
      console.error('Failed to acknowledge alert:', err);
    } finally {
      setAcknowledgingId(null);
    }
  };

  const getAlertStyles = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'critical':
        return {
          bg: 'bg-red-50',
          border: 'border-red-200',
          icon: <AlertCircle className="w-5 h-5 text-red-600 shrink-0" />,
          text: 'text-red-800',
          tag: 'bg-red-100 text-red-700'
        };
      case 'high':
        return {
          bg: 'bg-amber-50',
          border: 'border-amber-200',
          icon: <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0" />,
          text: 'text-amber-800',
          tag: 'bg-amber-100 text-amber-700'
        };
      default:
        return {
          bg: 'bg-blue-50',
          border: 'border-blue-200',
          icon: <Info className="w-5 h-5 text-blue-600 shrink-0" />,
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

  const unackCount = alerts.filter((a) => !a.acknowledged && (a.severity === 'critical' || a.severity === 'high')).length;

  return (
    <div className="bg-white rounded-lg shadow border border-slate-200 overflow-hidden flex flex-col h-full">
      <div className="p-4 border-b border-slate-200 bg-slate-50 flex justify-between items-center">
        <h3 className="font-semibold text-lg text-slate-800">System Alerts</h3>
        <span className="bg-red-100 text-red-700 py-0.5 px-2 rounded-full text-xs font-bold">
          {unackCount} Action Required
        </span>
      </div>
      <div className="p-4 space-y-3 overflow-y-auto flex-1">
        {alerts.map((alert) => {
          const styles = getAlertStyles(alert.severity);
          return (
            <div
              key={alert.id}
              className={`p-3 rounded-md border ${styles.bg} ${styles.border} flex gap-3 transition-opacity ${
                alert.acknowledged ? 'opacity-65' : 'opacity-100'
              }`}
            >
              <div className="mt-0.5">{styles.icon}</div>
              <div className="flex-1 min-w-0">
                <div className="flex justify-between items-start mb-1 gap-2">
                  <span className={`text-xs font-bold uppercase tracking-wider px-2 py-0.5 rounded ${styles.tag}`}>
                    {alert.severity}
                  </span>
                  <span className="text-xs text-slate-500 whitespace-nowrap">
                    {formatDistanceToNow(new Date(alert.timestamp))} ago
                  </span>
                </div>
                <p className={`font-semibold text-sm mb-1 ${styles.text}`}>{alert.message}</p>
                <div className="flex justify-between items-center gap-2 mt-2">
                  <p className="text-xs text-slate-600 truncate">
                    <span className="font-medium text-slate-700">{alert.source}</span>
                    {alert.details && <span> • {alert.details}</span>}
                  </p>
                  <div>
                    {alert.acknowledged ? (
                      <span className="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded">
                        <CheckCheck className="w-3 h-3" /> Ack
                      </span>
                    ) : (
                      <button
                        onClick={() => handleAcknowledge(alert.id)}
                        disabled={acknowledgingId === alert.id}
                        className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium rounded bg-white hover:bg-slate-50 border border-slate-300 text-slate-700 shadow-sm transition disabled:opacity-50 cursor-pointer"
                      >
                        <Check className="w-3 h-3 text-slate-500" />
                        {acknowledgingId === alert.id ? 'Saving...' : 'Acknowledge'}
                      </button>
                    )}
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

