import React from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { formatRelativeTime } from '../utils/dateTime';
import { AlertCircle, Clock, Bus, MapPin, Eye } from 'lucide-react';
import { Link } from 'react-router-dom';

// Custom SVG-based DivIcons for reliable offline rendering (no external CDN required)
function createColoredIcon(color, isPulsing = false) {
  return L.divIcon({
    className: 'custom-map-marker',
    html: `
      <div style="position: relative; width: 22px; height: 22px; display: flex; align-items: center; justify-content: center;">
        ${isPulsing ? `<span style="position: absolute; width: 100%; height: 100%; border-radius: 50%; background: ${color}; opacity: 0.4; animation: ping 1.5s cubic-bezier(0, 0, 0.2, 1) infinite;"></span>` : ''}
        <span style="width: 14px; height: 14px; border-radius: 50%; background: ${color}; border: 2.5px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.3); display: block;"></span>
      </div>
    `,
    iconSize: [22, 22],
    iconAnchor: [11, 11],
    popupAnchor: [0, -12],
  });
}

const redIcon = createColoredIcon('#ef4444', true);
const amberIcon = createColoredIcon('#f59e0b', false);
const blueIcon = createColoredIcon('#3b82f6', false);
const emeraldIcon = createColoredIcon('#10b981', false);

function getMarkerIcon(severity) {
  switch ((severity || '').toLowerCase()) {
    case 'critical':
    case 'high':
      return redIcon;
    case 'medium':
      return amberIcon;
    case 'low':
      return blueIcon;
    default:
      return emeraldIcon;
  }
}

export default function MiniMap({ events = [] }) {
  const center = [28.6139, 77.2090]; // Delhi Center

  return (
    <div className="w-full h-full relative z-0">
      <style>{`
        @keyframes ping {
          75%, 100% {
            transform: scale(2);
            opacity: 0;
          }
        }
        .leaflet-popup-content-wrapper {
          padding: 0;
          overflow: hidden;
          border-radius: 8px;
        }
        .leaflet-popup-content {
          margin: 0 !important;
          line-height: 1.4;
        }
      `}</style>
      <MapContainer
        center={center}
        zoom={11}
        className="w-full h-full"
        zoomControl={true}
        scrollWheelZoom={false}
      >
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>'
        />

        {events && events.map((event) => {
          const lat = event.latitude ?? event.lat;
          const lng = event.longitude ?? event.lng;
          if (lat == null || lng == null) return null;

          const isCritical = (event.severity || '').toLowerCase() === 'critical' || (event.severity || '').toLowerCase() === 'high';
          const icon = getMarkerIcon(event.severity);

          return (
            <React.Fragment key={`mini-${event.event_id || event.id || Math.random()}`}>
              {event.repeated_detections > 2 && (
                <Circle
                  center={[lat, lng]}
                  radius={500}
                  pathOptions={{
                    color: isCritical ? '#ef4444' : '#f59e0b',
                    fillColor: isCritical ? '#ef4444' : '#f59e0b',
                    fillOpacity: 0.25,
                    stroke: false,
                  }}
                />
              )}
              <Marker position={[lat, lng]} icon={icon}>
                <Popup>
                  <div className="w-64 text-slate-800 text-xs">
                    {/* Header */}
                    <div className="bg-slate-900 text-white p-2.5 flex items-center justify-between">
                      <div className="flex items-center gap-1.5 font-bold">
                        <AlertCircle className="w-3.5 h-3.5 text-amber-400" />
                        <span>{(event.event_type || 'Incident').toUpperCase()}</span>
                      </div>
                      <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold uppercase ${
                        isCritical ? 'bg-red-600 text-white' : 'bg-amber-500 text-white'
                      }`}>
                        {event.severity || 'Medium'}
                      </span>
                    </div>

                    {/* Evidence preview if available */}
                    {event.evidence && (
                      <div className="h-28 bg-slate-950 overflow-hidden relative">
                        <img
                          src={event.evidence}
                          alt={event.event_type}
                          className="w-full h-full object-cover"
                          onError={(e) => { e.currentTarget.style.display = 'none'; }}
                        />
                        <span className="absolute bottom-1 right-1 bg-black/70 text-white text-[9px] px-1.5 py-0.5 rounded font-mono">
                          Evidence Frame
                        </span>
                      </div>
                    )}

                    {/* Body */}
                    <div className="p-2.5 space-y-1.5 bg-white">
                      <div className="flex justify-between items-center text-slate-600">
                        <span className="flex items-center gap-1 font-semibold text-slate-800">
                          <Bus className="w-3 h-3 text-blue-600" />
                          {event.bus_id || 'BUS_021'}
                        </span>
                        <span className="flex items-center gap-1 text-[11px] text-slate-500">
                          <Clock className="w-3 h-3" />
                          {formatRelativeTime(event.timestamp)}
                        </span>
                      </div>

                      <div className="flex items-center gap-1 text-slate-500 font-mono text-[11px]">
                        <MapPin className="w-3 h-3 text-slate-400" />
                        <span>{lat.toFixed(4)}, {lng.toFixed(4)}</span>
                      </div>

                      <div className="pt-1.5 border-t border-slate-100 flex justify-between items-center">
                        <span className="text-[10px] text-slate-500 font-mono">
                          ID: {event.event_id || event.id}
                        </span>
                        <Link
                          to="/events"
                          className="text-blue-600 hover:text-blue-800 font-semibold flex items-center gap-0.5 text-[11px]"
                        >
                          <Eye className="w-3 h-3" /> View in Events
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

      {/* Floating hint pill */}
      <div className="absolute top-3 right-3 z-[400] pointer-events-none">
        <span className="bg-slate-900/80 backdrop-blur text-white text-[11px] font-medium px-2.5 py-1 rounded-full shadow border border-white/10 flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          Click dots for incident evidence
        </span>
      </div>
    </div>
  );
}
