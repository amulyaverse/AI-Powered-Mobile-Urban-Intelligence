import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { formatRelativeTime } from '../utils/dateTime';
import { AlertCircle, AlertTriangle, Info, Check, CheckCheck, ExternalLink, Bell, MapPin } from 'lucide-react';
import { acknowledgeAlert } from '../services/api';

function getAlertStyles(severity) {
  switch (severity?.toLowerCase()) {
    case 'critical':
      return {
        borderColor: '#ef4444',
        iconBg:      'bg-red-50 text-red-600',
        icon:        <AlertCircle className="w-4 h-4 text-red-600" />,
        tagBg:       'bg-red-100 text-red-700',
        titleColor:  'text-slate-800',
      };
    case 'high':
      return {
        borderColor: '#f59e0b',
        iconBg:      'bg-amber-50 text-amber-600',
        icon:        <AlertTriangle className="w-4 h-4 text-amber-600" />,
        tagBg:       'bg-amber-100 text-amber-800',
        titleColor:  'text-slate-800',
      };
    default:
      return {
        borderColor: '#3b82f6',
        iconBg:      'bg-blue-50 text-blue-600',
        icon:        <Info className="w-4 h-4 text-blue-600" />,
        tagBg:       'bg-blue-100 text-blue-800',
        titleColor:  'text-slate-700',
      };
  }
}

export default function AlertPanel({
  alerts: initialAlerts = [],
  onAcknowledge,
  onSelectEvent,
  selectedEventId,
}) {
  const [alerts, setAlerts] = useState(initialAlerts);
  const [acknowledgingId, setAcknowledgingId] = useState(null);

  React.useEffect(() => { setAlerts(initialAlerts); }, [initialAlerts]);

  const handleAcknowledge = async (id, e) => {
    if (e) e.stopPropagation();
    setAcknowledgingId(id);
    try {
      await acknowledgeAlert(id);
      setAlerts((prev) => prev.map((a) => (a.id === id ? { ...a, acknowledged: true } : a)));
      if (onAcknowledge) onAcknowledge(id);
    } catch (err) {
      console.error('Failed to acknowledge alert:', err);
    } finally {
      setAcknowledgingId(null);
    }
  };

  const unackCount = alerts.filter((a) => !a.acknowledged && (a.severity === 'critical' || a.severity === 'high')).length;

  if (!alerts || alerts.length === 0) {
    return (
      <div className="bg-white rounded-3xl shadow-card border border-gis-border p-8 text-center flex flex-col items-center gap-3 h-full">
        <div className="w-12 h-12 rounded-2xl bg-gis-sage-light flex items-center justify-center">
          <Bell className="w-5 h-5 text-gis-sage" />
        </div>
        <p className="text-gis-slate font-semibold text-sm">No active alerts</p>
        <p className="text-xs text-gis-slate/70">All systems nominal</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-3xl shadow-card border border-gis-border overflow-hidden flex flex-col h-full">
      {/* Header */}
      <div className="px-5 py-4 border-b border-gis-border flex justify-between items-center bg-gis-slate-light/40 shrink-0">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-2xl bg-red-100 flex items-center justify-center">
            <Bell className="w-4 h-4 text-red-600" />
          </div>
          <h3 className="font-extrabold text-base text-slate-800">System Alerts</h3>
        </div>
        {unackCount > 0 && (
          <span className="bg-red-100 text-red-700 px-3 py-1 rounded-full text-xs font-bold border border-red-200">
            {unackCount} Action Required
          </span>
        )}
      </div>

      {/* Alert list */}
      <div className="p-3 space-y-2.5 overflow-y-auto flex-1">
        {alerts.map((alert) => {
          const styles = getAlertStyles(alert.severity);

          let eventId = null;
          if (alert.id?.startsWith('ALT_EVT_') || alert.id?.startsWith('ALT_TRF_')) {
            eventId = alert.id.replace('ALT_', '');
          } else if (alert.id?.startsWith('EVT_') || alert.id?.startsWith('TRF_')) {
            eventId = alert.id;
          } else if (alert.message?.includes('EVT_') || alert.message?.includes('TRF_')) {
            const match = alert.message.match(/(?:EVT_|TRF_)[a-zA-Z0-9_-]+/);
            if (match) eventId = match[0];
          }

          const isSelected = selectedEventId && (selectedEventId === eventId);

          return (
            <div
              key={alert.id}
              onClick={() => {
                if (eventId && onSelectEvent) onSelectEvent(eventId);
              }}
              className={`rounded-2xl border transition-all duration-200 p-3.5 flex gap-3 ${
                eventId ? 'cursor-pointer hover:shadow-card' : ''
              } ${
                isSelected
                  ? 'border-blue-500 bg-blue-50/50 ring-2 ring-blue-400/30'
                  : 'border-gis-border bg-white hover:bg-slate-50/70'
              } ${alert.acknowledged ? 'opacity-60' : 'opacity-100'}`}
              style={{ borderLeftWidth: '4px', borderLeftColor: styles.borderColor }}
            >
              {/* Icon */}
              <div className={`w-7 h-7 rounded-xl flex items-center justify-center shrink-0 mt-0.5 ${styles.iconBg}`}>
                {styles.icon}
              </div>

              {/* Content */}
              <div className="flex-1 min-w-0">
                <div className="flex justify-between items-center mb-1.5 gap-2">
                  <span className={`text-[10px] font-bold uppercase tracking-wide px-2 py-0.5 rounded-full ${styles.tagBg}`}>
                    {alert.severity}
                  </span>
                  <span className="text-[11px] text-gis-slate whitespace-nowrap font-semibold">
                    {formatRelativeTime(alert.timestamp)}
                  </span>
                </div>

                <p className={`font-bold text-sm mb-1 leading-snug ${styles.titleColor}`}>{alert.message}</p>

                <p className="text-xs text-gis-slate truncate">
                  <span className="font-semibold text-slate-600">{alert.source}</span>
                  {alert.details && <span className="text-gis-slate/80"> · {alert.details}</span>}
                </p>

                {/* Actions */}
                <div className="flex items-center gap-2 mt-2.5" onClick={(e) => e.stopPropagation()}>
                  {eventId && (
                    <button
                      type="button"
                      onClick={() => onSelectEvent && onSelectEvent(eventId)}
                      className={`inline-flex items-center gap-1 px-2.5 py-1 text-[11px] font-bold rounded-xl border transition-colors ${
                        isSelected
                          ? 'bg-blue-600 text-white border-blue-600'
                          : 'text-blue-700 bg-blue-50 hover:bg-blue-600 hover:text-white border-blue-200'
                      }`}
                      title="Center and focus on Map"
                    >
                      <MapPin className="w-3 h-3" />
                      Focus Map
                    </button>
                  )}

                  {eventId && (
                    <Link
                      to="/events"
                      state={{ selectedEventId: eventId }}
                      className="inline-flex items-center gap-1 px-2.5 py-1 text-[11px] font-bold text-slate-700 bg-slate-100 hover:bg-slate-800 hover:text-white border border-slate-200 rounded-xl transition-all duration-150"
                    >
                      <ExternalLink className="w-3 h-3" />
                      Inspect
                    </Link>
                  )}

                  {alert.acknowledged ? (
                    <span className="inline-flex items-center gap-1 text-[11px] font-bold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-xl">
                      <CheckCheck className="w-3 h-3" /> Acknowledged
                    </span>
                  ) : (
                    <button
                      onClick={(e) => handleAcknowledge(alert.id, e)}
                      disabled={acknowledgingId === alert.id}
                      className="inline-flex items-center gap-1 px-2.5 py-1 text-[11px] font-bold rounded-xl bg-slate-100 hover:bg-slate-800 hover:text-white border border-slate-200 text-slate-600 transition-all duration-150 disabled:opacity-50 cursor-pointer ml-auto"
                    >
                      <Check className="w-3 h-3" />
                      {acknowledgingId === alert.id ? 'Saving…' : 'Acknowledge'}
                    </button>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
