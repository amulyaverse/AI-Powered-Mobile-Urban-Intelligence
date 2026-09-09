import React, { useEffect, useMemo, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { formatRelativeTime, formatDateTime } from '../utils/dateTime';
import { AlertCircle, Clock, Bus, MapPin, Eye, Radio, ShieldAlert } from 'lucide-react';
import { Link } from 'react-router-dom';

// ── Coordinate Validation Helper ──────────────────────────────────────────────
function isValidCoord(lat, lng) {
  return (
    typeof lat === 'number' &&
    typeof lng === 'number' &&
    !isNaN(lat) &&
    !isNaN(lng) &&
    lat >= -90 &&
    lat <= 90 &&
    lng >= -180 &&
    lng <= 180 &&
    (lat !== 0 || lng !== 0)
  );
}

// ── Custom SVG DivIcon Creator (100% offline & CDN-independent) ───────────────
function createMarkerIcon({ color, label = '', isPulsing = false, isSelected = false, iconType = 'dot' }) {
  const size = isSelected ? 32 : 24;
  const pulseSize = size + 16;

  return L.divIcon({
    className: 'custom-urban-marker',
    html: `
      <div style="position: relative; width: ${size}px; height: ${size}px; display: flex; align-items: center; justify-content: center;">
        ${(isPulsing || isSelected) ? `
          <span style="
            position: absolute;
            width: ${pulseSize}px;
            height: ${pulseSize}px;
            border-radius: 50%;
            background: ${color};
            opacity: ${isSelected ? '0.55' : '0.35'};
            animation: ping 1.6s cubic-bezier(0, 0, 0.2, 1) infinite;
          "></span>
        ` : ''}
        <div style="
          width: ${size}px;
          height: ${size}px;
          border-radius: 50%;
          background: ${color};
          border: ${isSelected ? '3px solid #ffffff' : '2.5px solid #ffffff'};
          box-shadow: 0 ${isSelected ? '4px 12px' : '2px 6px'} rgba(0,0,0,0.35);
          display: flex;
          align-items: center;
          justify-content: center;
          color: #ffffff;
          font-weight: 800;
          font-size: ${size > 24 ? '11px' : '9px'};
          font-family: system-ui, -apple-system, sans-serif;
        ">
          ${label ? label : (iconType === 'traffic' ? '🚗' : iconType === 'defect' ? '⚠️' : '')}
        </div>
      </div>
    `,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
    popupAnchor: [0, -size / 2 - 4],
  });
}

// Palette colors aligned with UrbanPulse design tokens
const SEVERITY_COLORS = {
  critical: '#ef4444', // red
  high:     '#ef4444', // red
  medium:   '#f59e0b', // amber
  low:      '#10b981', // emerald
  traffic:  '#3b82f6', // blue
};

function getIncidentIcon(event, isSelected = false) {
  const type = (event.event_type || '').toLowerCase();
  const sev = (event.severity || 'medium').toLowerCase();
  const isTraffic = ['congestion', 'vehicle_count', 'traffic_snapshot', 'traffic'].includes(type);
  const color = isTraffic ? SEVERITY_COLORS.traffic : (SEVERITY_COLORS[sev] || SEVERITY_COLORS.medium);
  const isPulsing = sev === 'critical' || sev === 'high' || isSelected;
  const label = event.repeated_detections > 1 ? `${event.repeated_detections}×` : '';

  return createMarkerIcon({
    color,
    label,
    isPulsing,
    isSelected,
    iconType: isTraffic ? 'traffic' : 'defect',
  });
}

// ── Map View Controller Hook ──────────────────────────────────────────────────
function MapViewController({ selectedEvent, defaultCenter }) {
  const map = useMap();
  const prevSelectedIdRef = useRef(null);

  useEffect(() => {
    if (!selectedEvent) return;
    const lat = selectedEvent.latitude ?? selectedEvent.lat;
    const lng = selectedEvent.longitude ?? selectedEvent.lng;

    if (isValidCoord(lat, lng) && prevSelectedIdRef.current !== (selectedEvent.event_id || selectedEvent.id)) {
      prevSelectedIdRef.current = selectedEvent.event_id || selectedEvent.id;
      map.flyTo([lat, lng], Math.max(map.getZoom(), 14), {
        duration: 0.8,
        easeLinearity: 0.25,
      });
    }
  }, [selectedEvent, map]);

  return null;
}

export default function MiniMap({
  events = [],
  selectedEventId = null,
  onSelectEvent = null,
}) {
  const defaultCenter = [28.6139, 77.2090]; // Central Delhi

  // Filter only items with genuine numeric GPS coordinates
  const validEvents = useMemo(() => {
    return (events || []).filter((e) => {
      const lat = e.latitude ?? e.lat;
      const lng = e.longitude ?? e.lng;
      return isValidCoord(lat, lng);
    });
  }, [events]);

  const selectedEvent = useMemo(() => {
    if (!selectedEventId) return null;
    return validEvents.find((e) => (e.event_id || e.id) === selectedEventId) || null;
  }, [validEvents, selectedEventId]);

  return (
    <div className="w-full h-full relative z-0">
      <style>{`
        @keyframes ping {
          75%, 100% {
            transform: scale(2.2);
            opacity: 0;
          }
        }
        .leaflet-popup-content-wrapper {
          padding: 0 !important;
          overflow: hidden !important;
          border-radius: 16px !important;
          box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.2), 0 8px 10px -6px rgba(0, 0, 0, 0.1) !important;
        }
        .leaflet-popup-content {
          margin: 0 !important;
          line-height: 1.4 !important;
        }
      `}</style>

      <MapContainer
        center={defaultCenter}
        zoom={12}
        className="w-full h-full"
        zoomControl={true}
        scrollWheelZoom={false}
      >
        {/* Standard OpenStreetMap Leaflet TileLayer — No API Key Required */}
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          maxZoom={19}
        />

        <MapViewController
          selectedEvent={selectedEvent}
          defaultCenter={defaultCenter}
        />

        {validEvents.map((event) => {
          const lat = event.latitude ?? event.lat;
          const lng = event.longitude ?? event.lng;
          const eventId = event.event_id || event.id;
          const isSelected = selectedEventId && (selectedEventId === eventId);
          const icon = getIncidentIcon(event, isSelected);
          const sev = (event.severity || 'medium').toLowerCase();
          const isCritical = sev === 'critical' || sev === 'high';
          const isTraffic = ['congestion', 'vehicle_count', 'traffic_snapshot', 'traffic'].includes((event.event_type || '').toLowerCase());

          return (
            <React.Fragment key={`minimap-evt-${eventId}`}>
              {/* Fleet Corroboration Spatial Ring */}
              {event.repeated_detections > 1 && (
                <Circle
                  center={[lat, lng]}
                  radius={Math.min(300, 70 + (event.repeated_detections * 25))}
                  pathOptions={{
                    color: isCritical ? '#ef4444' : '#f59e0b',
                    fillColor: isCritical ? '#ef4444' : '#f59e0b',
                    fillOpacity: 0.16,
                    weight: 1.5,
                    dashArray: '3 3',
                  }}
                />
              )}

              <Marker
                position={[lat, lng]}
                icon={icon}
                eventHandlers={{
                  click: () => {
                    if (onSelectEvent) onSelectEvent(eventId);
                  },
                }}
              >
                <Popup>
                  <div className="w-72 font-sans bg-white text-slate-800 text-xs">
                    {/* Header */}
                    <div
                      className="p-3 flex items-center justify-between text-white"
                      style={{
                        backgroundColor: isTraffic ? '#2563eb' : (isCritical ? '#dc2626' : '#d97706'),
                      }}
                    >
                      <div className="flex items-center gap-1.5 font-extrabold text-sm tracking-tight capitalize">
                        {isTraffic ? <Radio className="w-4 h-4 text-blue-200" /> : <AlertCircle className="w-4 h-4 text-amber-200" />}
                        <span>{(event.event_type || 'Incident').replace('_', ' ')}</span>
                      </div>
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider bg-white/20 text-white">
                        {event.severity || 'Medium'}
                      </span>
                    </div>

                    {/* Fleet Corroboration Alert Banner */}
                    {event.repeated_detections > 1 && (
                      <div className="bg-amber-50 border-b border-amber-200 px-3 py-1.5 flex items-center gap-1.5 text-amber-900 text-[11px] font-bold">
                        <ShieldAlert className="w-3.5 h-3.5 text-amber-600 shrink-0" />
                        <span>Fleet Corroboration: {event.repeated_detections}× observations</span>
                      </div>
                    )}

                    {/* Evidence Frame Preview */}
                    {event.evidence && (
                      <div className="h-32 bg-slate-950 overflow-hidden relative group">
                        <img
                          src={event.evidence}
                          alt={event.event_type}
                          className="w-full h-full object-cover"
                          onError={(e) => { e.currentTarget.style.display = 'none'; }}
                        />
                        <span className="absolute bottom-1.5 right-1.5 bg-black/75 text-white text-[9px] px-1.5 py-0.5 rounded font-mono font-bold">
                          AI Capture · {Math.round((event.confidence || 0.85) * 100)}% Conf
                        </span>
                      </div>
                    )}

                    {/* Metadata Grid */}
                    <div className="p-3 space-y-2 bg-white">
                      <div className="grid grid-cols-2 gap-2 text-[11px]">
                        <div>
                          <span className="text-slate-400 block font-semibold text-[10px] uppercase">Bus Sensor</span>
                          <span className="font-bold text-slate-800 flex items-center gap-1 mt-0.5">
                            <Bus className="w-3 h-3 text-blue-600 shrink-0" />
                            {event.bus_id || 'BUS_021'}
                          </span>
                        </div>
                        <div>
                          <span className="text-slate-400 block font-semibold text-[10px] uppercase">Confidence</span>
                          <span className="font-bold text-slate-800 mt-0.5 block">
                            {Math.round((event.confidence || 0.85) * 100)}%
                          </span>
                        </div>
                      </div>

                      <div className="pt-1.5 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500 font-mono">
                        <span className="flex items-center gap-1">
                          <MapPin className="w-3 h-3 text-slate-400" />
                          {lat.toFixed(4)}, {lng.toFixed(4)}
                        </span>
                        <span className="capitalize font-bold px-1.5 py-0.5 rounded text-[10px] bg-slate-100 text-slate-700">
                          {event.status || 'New'}
                        </span>
                      </div>

                      {event.timestamp && (
                        <div className="text-[10px] text-slate-400 flex items-center gap-1">
                          <Clock className="w-3 h-3 text-slate-400" />
                          <span>{formatDateTime(event.timestamp, 'dd MMM yyyy, HH:mm')} · {formatRelativeTime(event.timestamp)}</span>
                        </div>
                      )}

                      <div className="pt-2 border-t border-slate-100">
                        <Link
                          to="/events"
                          state={{ selectedEventId: eventId }}
                          className="w-full bg-slate-800 hover:bg-slate-900 text-white font-bold py-1.5 rounded-xl flex items-center justify-center gap-1 text-[11px] transition-colors"
                        >
                          <Eye className="w-3 h-3" /> Inspect Event Details
                        </Link>
                      </div>
                    </div>
                  </div>
                </Popup>
              </Marker>
            </React.Fragment>
          );
        })}
      </MapContainer>

      {/* Floating Status Badge */}
      <div className="absolute top-3 right-3 z-[400] pointer-events-none flex flex-col items-end gap-1.5">
        <span className="glass-card text-slate-700 text-[11px] font-bold px-3 py-1.5 rounded-full shadow-card border border-gis-border flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-gis-sage animate-pulse" />
          <span>{validEvents.length} Active Detections</span>
        </span>
      </div>
    </div>
  );
}
