/**
 * LiveEventTicker.jsx
 * --------------------
 * Animated slide-in ticker that displays real-time AI detection events
 * as they arrive over the WebSocket event feed.
 *
 * Each card shows:
 *   - Detection type badge (pothole, vehicle_count, road_defect)
 *   - Confidence percentage
 *   - Severity colour coding
 *   - Bus ID and GPS coordinates
 *   - Time elapsed since detection
 *
 * Props:
 *   events       {Array}   — array of event objects (newest-first)
 *   maxVisible   {number}  — max cards to show (default: 5)
 *   className    {string}  — additional CSS classes
 */

import React, { useEffect, useState } from 'react';
import { AlertTriangle, Car, MapPin, Radio, Clock } from 'lucide-react';
import { formatRelativeTime } from '../utils/dateTime';

const TYPE_STYLES = {
  pothole:       { bg: 'bg-rose-50',    border: 'border-rose-200',    text: 'text-rose-700',    badge: 'bg-rose-500',    label: 'Pothole',       Icon: AlertTriangle },
  road_defect:   { bg: 'bg-amber-50',   border: 'border-amber-200',   text: 'text-amber-700',   badge: 'bg-amber-500',   label: 'Road Defect',   Icon: AlertTriangle },
  vehicle_count:    { bg: 'bg-blue-50',    border: 'border-blue-200',    text: 'text-blue-700',    badge: 'bg-blue-500',    label: 'Traffic Scan',  Icon: Car },
  traffic_snapshot: { bg: 'bg-blue-50',    border: 'border-blue-200',    text: 'text-blue-700',    badge: 'bg-blue-500',    label: 'Traffic Scan',  Icon: Car },
  congestion:       { bg: 'bg-orange-50',  border: 'border-orange-200',  text: 'text-orange-700',  badge: 'bg-orange-500',  label: 'Congestion',    Icon: Radio },
};

const SEVERITY_DOT = {
  low:      'bg-emerald-400',
  medium:   'bg-amber-400',
  high:     'bg-orange-500',
  critical: 'bg-rose-600',
};

function EventCard({ event, index }) {
  const [visible, setVisible] = useState(false);

  // Slide in after a short stagger delay
  useEffect(() => {
    const t = setTimeout(() => setVisible(true), index * 60);
    return () => clearTimeout(t);
  }, [index]);

  const style = TYPE_STYLES[event.event_type] || TYPE_STYLES.pothole;
  const { Icon } = style;
  const timeAgo = formatRelativeTime(event.timestamp);

  return (
    <div
      className={`
        transition-all duration-300 ease-out
        ${visible ? 'opacity-100 translate-y-0' : 'opacity-0 -translate-y-2'}
        ${style.bg} ${style.border} border rounded-lg p-3 flex gap-3 items-start
      `}
    >
      {/* Icon */}
      <div className={`${style.badge} rounded-md p-1.5 shrink-0 mt-0.5`}>
        <Icon className="w-3.5 h-3.5 text-white" />
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between gap-2 mb-1">
          <div className="flex items-center gap-1.5">
            <span className={`text-xs font-bold ${style.text}`}>{style.label}</span>
            <span
              className={`w-2 h-2 rounded-full shrink-0 ${SEVERITY_DOT[event.severity] || 'bg-slate-400'}`}
              title={`Severity: ${event.severity}`}
            />
          </div>
          <span className="text-[11px] text-slate-400 font-mono shrink-0">
            {Math.round(event.confidence * 100)}% conf
          </span>
        </div>

        <div className="flex items-center gap-1 text-[11px] text-slate-500 mb-1">
          <MapPin className="w-3 h-3 shrink-0" />
          <span className="font-mono truncate">
            {typeof event.latitude === 'number' ? event.latitude.toFixed(4) : '—'},&nbsp;
            {typeof event.longitude === 'number' ? event.longitude.toFixed(4) : '—'}
          </span>
        </div>

        <div className="flex items-center justify-between">
          <span className="text-[11px] text-slate-500 font-medium">
            {event.bus_id || 'Unknown Bus'}
          </span>
          <div className="flex items-center gap-1 text-[10px] text-slate-400">
            <Clock className="w-3 h-3" />
            {timeAgo}
          </div>
        </div>

        {/* Traffic detail row */}
        {event.event_type === 'vehicle_count' && event.total_vehicles != null && (
          <div className="mt-1.5 text-[10px] text-slate-500 flex gap-2 flex-wrap">
            <span>🚗 {event.car_count ?? 0}</span>
            <span>🛵 {event.bike_count ?? 0}</span>
            <span>🚌 {event.bus_count ?? 0}</span>
            <span>🚛 {event.truck_count ?? 0}</span>
            <span className="font-semibold text-slate-600">Total: {event.total_vehicles}</span>
            {event.density && (
              <span className={`font-bold ${style.text}`}>{event.density}</span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default function LiveEventTicker({ events = [], maxVisible = 5, className = '' }) {
  const visible = events.slice(0, maxVisible);

  if (visible.length === 0) {
    return (
      <div className={`flex flex-col items-center justify-center py-8 text-slate-400 ${className}`}>
        <Radio className="w-8 h-8 mb-2 opacity-30 animate-pulse" />
        <p className="text-sm font-medium">Waiting for AI detections…</p>
        <p className="text-xs mt-1 opacity-70">Events will appear here as bus cameras send frames</p>
      </div>
    );
  }

  return (
    <div className={`space-y-2 ${className}`}>
      {visible.map((event, i) => (
        <EventCard
          key={event.event_id || `${event.timestamp}-${i}`}
          event={event}
          index={i}
        />
      ))}
    </div>
  );
}
