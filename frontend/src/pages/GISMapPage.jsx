import React, { useEffect, useState, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { MapContainer, TileLayer, Marker, Popup, Circle, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { getEvents, getHotspots, getBuses } from '../services/api';
import { useEventWebSocket } from '../hooks/useEventWebSocket';
import {
  Flame,
  Clock,
  Navigation,
  Bus as BusIcon,
  Search,
  Maximize2,
  MapPin,
  RefreshCw,
  Radio,
  Wifi,
  ShieldAlert,
  Eye,
  Crosshair,
  AlertCircle
} from 'lucide-react';
import { LoadingState, ErrorState } from '../components/PageStatusState';
import { formatDateTime, formatRelativeTime } from '../utils/dateTime';

// ── Fix Leaflet Default Icon Assets ───────────────────────────────────────────
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl:       'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl:     'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

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

// ── Custom SVG DivIcons ───────────────────────────────────────────────────────
function createSvgMarker({ color, label = '', isPulsing = false, iconType = 'defect', size = 26 }) {
  const pulseSize = size + 16;
  return L.divIcon({
    className: 'custom-gis-marker',
    html: `
      <div style="position: relative; width: ${size}px; height: ${size}px; display: flex; align-items: center; justify-content: center;">
        ${isPulsing ? `
          <span style="
            position: absolute;
            width: ${pulseSize}px;
            height: ${pulseSize}px;
            border-radius: 50%;
            background: ${color};
            opacity: 0.35;
            animation: ping 1.6s cubic-bezier(0, 0, 0.2, 1) infinite;
          "></span>
        ` : ''}
        <div style="
          width: ${size}px;
          height: ${size}px;
          border-radius: 50%;
          background: ${color};
          border: 2.5px solid #ffffff;
          box-shadow: 0 2px 8px rgba(0,0,0,0.32);
          display: flex;
          align-items: center;
          justify-content: center;
          color: #ffffff;
          font-weight: 800;
          font-size: ${label ? '9px' : '11px'};
          font-family: system-ui, -apple-system, sans-serif;
        ">
          ${label || (iconType === 'traffic' ? '🚗' : iconType === 'bus' ? '🚌' : '⚠️')}
        </div>
      </div>
    `,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
    popupAnchor: [0, -size / 2 - 4],
  });
}

function createBusMarker(busId) {
  return L.divIcon({
    className: 'custom-gis-bus-marker',
    html: `
      <div style="
        display: inline-flex;
        align-items: center;
        gap: 4px;
        background: #312e81;
        color: #ffffff;
        padding: 3px 8px;
        border-radius: 9999px;
        border: 2px solid #ffffff;
        box-shadow: 0 3px 10px rgba(0,0,0,0.35);
        font-size: 10px;
        font-weight: 800;
        font-family: system-ui, -apple-system, sans-serif;
        white-space: nowrap;
      ">
        <span style="font-size: 12px;">🚌</span>
        <span>${busId}</span>
      </div>
    `,
    iconSize: [80, 24],
    iconAnchor: [40, 12],
    popupAnchor: [0, -14],
  });
}

const SEVERITY_COLORS = {
  critical: '#ef4444',
  high:     '#ef4444',
  medium:   '#f59e0b',
  low:      '#10b981',
  traffic:  '#3b82f6',
};

const HOTSPOT_STYLES = {
  critical: { stroke: '#ef4444', fill: '#ef4444' },
  high:     { stroke: '#ef4444', fill: '#ef4444' },
  medium:   { stroke: '#f59e0b', fill: '#f59e0b' },
  low:      { stroke: '#10b981', fill: '#10b981' },
};

// ── Map Controller Component for programmatic zoom & bounds ──────────────────
function MapController({ fitBoundsTrigger, centerDelhiTrigger, elements }) {
  const map = useMap();

  useEffect(() => {
    if (centerDelhiTrigger > 0) {
      map.setView([28.6139, 77.2090], 12, { animate: true });
    }
  }, [centerDelhiTrigger, map]);

  useEffect(() => {
    if (fitBoundsTrigger > 0 && elements && elements.length > 0) {
      const coords = elements
        .map((item) => {
          const lat = item.latitude ?? item.center_lat ?? item.last_lat ?? item.lat;
          const lng = item.longitude ?? item.center_lng ?? item.last_lng ?? item.lng;
          return isValidCoord(lat, lng) ? [lat, lng] : null;
        })
        .filter(Boolean);

      if (coords.length > 0) {
        const bounds = L.latLngBounds(coords);
        map.fitBounds(bounds, { padding: [40, 40], maxZoom: 15 });
      }
    }
  }, [fitBoundsTrigger, elements, map]);

  return null;
}

export default function GISMapPage() {
  const navigate = useNavigate();
  const [events, setEvents]             = useState([]);
  const [hotspots, setHotspots]         = useState([]);
  const [buses, setBuses]               = useState([]);

  // Layer toggles
  const [showEvents, setShowEvents]     = useState(true);
  const [showHotspots, setShowHotspots] = useState(true);
  const [showBuses, setShowBuses]       = useState(true);

  // Filters
  const [selectedType, setSelectedType] = useState('all'); // all | pothole | road_defect | congestion
  const [selectedSev, setSelectedSev]   = useState('all');  // all | critical | high | medium | low
  const [timeFilter, setTimeFilter]     = useState('all');   // all | today | 2h | recent
  const [searchTerm, setSearchTerm]     = useState('');

  // Map action triggers
  const [fitBoundsTrigger, setFitBoundsTrigger] = useState(0);
  const [centerDelhiTrigger, setCenterDelhiTrigger] = useState(0);

  const [loading, setLoading]           = useState(true);
  const [error, setError]               = useState(null);

  const defaultCenter = [28.6139, 77.2090]; // Delhi Center

  const { latestEvent, isConnected: isWsConnected } = useEventWebSocket();

  // Load real data from backend
  const loadData = useCallback(async (isInitial = false) => {
    if (isInitial) setLoading(true);
    try {
      const [eventsData, hotspotsData, busesData] = await Promise.all([
        getEvents({ limit: 100 }),
        getHotspots('all'),
        getBuses(),
      ]);
      setEvents(eventsData || []);
      setHotspots(hotspotsData || []);
      setBuses(busesData || []);
      setError(null);
    } catch (err) {
      console.error('[GISMap] Failed to load GIS data:', err);
      if (isInitial) setError(err.message || 'Failed to load GIS map layers.');
    } finally {
      if (isInitial) setLoading(false);
    }
  }, []);

  useEffect(() => { loadData(true); }, [loadData]);

  // Periodic refresh as fallback
  useEffect(() => {
    const poller = setInterval(() => loadData(false), 10000);
    return () => clearInterval(poller);
  }, [loadData]);

  // Real-time event ingestion over WebSocket
  useEffect(() => {
    if (!latestEvent?.event_id) return;
    const lat = latestEvent.latitude ?? latestEvent.lat;
    const lng = latestEvent.longitude ?? latestEvent.lng;
    if (!isValidCoord(lat, lng)) return;

    setEvents((prev) => {
      const filtered = prev.filter((e) => (e.event_id || e.id) !== latestEvent.event_id);
      return [latestEvent, ...filtered];
    });
  }, [latestEvent]);

  // Filtered Events
  const filteredEvents = useMemo(() => {
    const now = Date.now();
    return events.filter((e) => {
      const lat = e.latitude ?? e.lat;
      const lng = e.longitude ?? e.lng;
      if (!isValidCoord(lat, lng)) return false;

      // Type filter
      const type = (e.event_type || '').toLowerCase();
      if (selectedType === 'pothole' && type !== 'pothole') return false;
      if (selectedType === 'road_defect' && !['road_defect', 'crack'].includes(type)) return false;
      if (selectedType === 'congestion' && !['congestion', 'vehicle_count', 'traffic_snapshot', 'traffic'].includes(type)) return false;

      // Severity filter
      const sev = (e.severity || '').toLowerCase();
      if (selectedSev === 'critical' && sev !== 'critical') return false;
      if (selectedSev === 'high' && !['high', 'critical'].includes(sev)) return false;
      if (selectedSev === 'medium' && sev !== 'medium') return false;
      if (selectedSev === 'low' && sev !== 'low') return false;

      // Time filter
      if (timeFilter !== 'all' && e.timestamp) {
        const itemTime = new Date(e.timestamp).getTime();
        if (!isNaN(itemTime)) {
          const diffMin = (now - itemTime) / 60000;
          if (timeFilter === 'recent' && diffMin > 30) return false;
          if (timeFilter === '2h' && diffMin > 120) return false;
          if (timeFilter === 'today' && diffMin > 1440) return false;
        }
      }

      // Search filter
      if (searchTerm.trim()) {
        const q = searchTerm.toLowerCase().trim();
        const matchId = (e.event_id || e.id || '').toLowerCase().includes(q);
        const matchBus = (e.bus_id || '').toLowerCase().includes(q);
        const matchType = (e.event_type || '').toLowerCase().includes(q);
        if (!matchId && !matchBus && !matchType) return false;
      }

      return true;
    });
  }, [events, selectedType, selectedSev, timeFilter, searchTerm]);

  // Valid Hotspots
  const validHotspots = useMemo(() => {
    return hotspots.filter((h) => {
      const lat = h.center_lat ?? h.latitude ?? h.lat;
      const lng = h.center_lng ?? h.longitude ?? h.lng;
      return isValidCoord(lat, lng);
    });
  }, [hotspots]);

  // Valid Buses
  const validBuses = useMemo(() => {
    return buses.filter((b) => {
      const lat = b.last_lat ?? b.lat;
      const lng = b.last_lng ?? b.lng;
      return isValidCoord(lat, lng);
    });
  }, [buses]);

  // All valid elements for auto-bounds
  const allVisibleElements = useMemo(() => {
    const list = [];
    if (showEvents) list.push(...filteredEvents);
    if (showHotspots) list.push(...validHotspots);
    if (showBuses) list.push(...validBuses);
    return list;
  }, [showEvents, filteredEvents, showHotspots, validHotspots, showBuses, validBuses]);

  if (loading && events.length === 0 && hotspots.length === 0) {
    return <LoadingState message="Loading Urban GIS map layers and real-time fleet telemetry..." />;
  }

  if (error && events.length === 0 && hotspots.length === 0) {
    return (
      <ErrorState
        title="GIS Map Unavailable"
        message="Could not load spatial map layers from backend."
        onRetry={() => loadData(true)}
      />
    );
  }

  return (
    <div className="space-y-4">
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

      {/* ── Top Header & Telemetry Status ───────────────────────── */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
        <div>
          <h2 className="text-2xl font-extrabold text-slate-800 tracking-tight flex items-center gap-2">
            <span>Urban Intelligence GIS Layer</span>
            <span className="text-xs bg-indigo-100 text-indigo-800 font-bold px-2.5 py-0.5 rounded-full uppercase tracking-wider">
              OpenStreetMap
            </span>
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Real-time geospatial intelligence aggregated from mobile bus sensors across the transit grid
          </p>
        </div>

        <div className="flex items-center gap-2">
          {isWsConnected ? (
            <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <Wifi className="w-3.5 h-3.5" />
              <span>Live Sensing Feed</span>
            </span>
          ) : (
            <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-slate-100 text-slate-600 border border-slate-200">
              <Radio className="w-3.5 h-3.5" />
              <span>Synchronized</span>
            </span>
          )}

          <button
            onClick={() => loadData(false)}
            className="p-2 rounded-xl bg-white border border-gis-border text-slate-600 hover:text-slate-900 hover:bg-slate-50 shadow-sm transition-colors cursor-pointer"
            title="Refresh GIS Data"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* ── Filter & Layer Control Bar ──────────────────────────── */}
      <div className="bg-white rounded-2xl border border-gis-border p-3.5 shadow-card flex flex-wrap items-center justify-between gap-3">
        {/* Quick Filters */}
        <div className="flex flex-wrap items-center gap-2 text-xs">
          {/* Search Box */}
          <div className="relative min-w-[170px]">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search Event / Bus ID..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-8 pr-2.5 py-1.5 rounded-xl border border-slate-200 bg-slate-50 text-xs text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 w-full"
            />
          </div>

          {/* Event Type */}
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="px-2.5 py-1.5 rounded-xl border border-slate-200 bg-slate-50 text-xs font-semibold text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500/30"
          >
            <option value="all">All Event Types</option>
            <option value="pothole">Potholes</option>
            <option value="road_defect">Road Defects</option>
            <option value="congestion">Traffic / Congestion</option>
          </select>

          {/* Severity */}
          <select
            value={selectedSev}
            onChange={(e) => setSelectedSev(e.target.value)}
            className="px-2.5 py-1.5 rounded-xl border border-slate-200 bg-slate-50 text-xs font-semibold text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500/30"
          >
            <option value="all">All Severities</option>
            <option value="critical">Critical</option>
            <option value="high">High & Critical</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>

          {/* Time Filter */}
          <select
            value={timeFilter}
            onChange={(e) => setTimeFilter(e.target.value)}
            className="px-2.5 py-1.5 rounded-xl border border-slate-200 bg-slate-50 text-xs font-semibold text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500/30"
          >
            <option value="all">All Time</option>
            <option value="today">Today</option>
            <option value="2h">Last 2 Hours</option>
            <option value="recent">Recent (&lt; 30m)</option>
          </select>
        </div>

        {/* Layer Toggles & Map Actions */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Layer Checkboxes */}
          <label className="inline-flex items-center gap-1.5 text-xs font-bold text-slate-700 cursor-pointer select-none bg-slate-50 px-2.5 py-1.5 rounded-xl border border-slate-200">
            <input
              type="checkbox"
              checked={showEvents}
              onChange={(e) => setShowEvents(e.target.checked)}
              className="rounded text-blue-600 focus:ring-blue-500"
            />
            <span>Detections ({filteredEvents.length})</span>
          </label>

          <label className="inline-flex items-center gap-1.5 text-xs font-bold text-slate-700 cursor-pointer select-none bg-slate-50 px-2.5 py-1.5 rounded-xl border border-slate-200">
            <input
              type="checkbox"
              checked={showHotspots}
              onChange={(e) => setShowHotspots(e.target.checked)}
              className="rounded text-amber-600 focus:ring-amber-500"
            />
            <span className="flex items-center gap-1">
              <Flame className="w-3.5 h-3.5 text-amber-500" />
              <span>Persistent Hotspot Clusters ({validHotspots.length})</span>
            </span>
          </label>

          <label className="inline-flex items-center gap-1.5 text-xs font-bold text-slate-700 cursor-pointer select-none bg-slate-50 px-2.5 py-1.5 rounded-xl border border-slate-200">
            <input
              type="checkbox"
              checked={showBuses}
              onChange={(e) => setShowBuses(e.target.checked)}
              className="rounded text-indigo-600 focus:ring-indigo-500"
            />
            <span className="flex items-center gap-1">
              <BusIcon className="w-3.5 h-3.5 text-indigo-600" />
              <span>Bus Fleet ({validBuses.length})</span>
            </span>
          </label>

          {/* Map Controls */}
          <button
            onClick={() => setCenterDelhiTrigger((t) => t + 1)}
            className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-xl text-xs font-bold text-slate-700 bg-slate-100 hover:bg-slate-200 transition-colors cursor-pointer"
            title="Center on Delhi"
          >
            <Crosshair className="w-3.5 h-3.5" />
            <span>Delhi</span>
          </button>

          <button
            onClick={() => setFitBoundsTrigger((t) => t + 1)}
            className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-xl text-xs font-bold text-blue-700 bg-blue-50 hover:bg-blue-100 border border-blue-200 transition-colors cursor-pointer"
            title="Fit view to visible items"
          >
            <Maximize2 className="w-3.5 h-3.5" />
            <span>Fit Bounds</span>
          </button>
        </div>
      </div>

      {/* ── Main Map Canvas ─────────────────────────────────────── */}
      <div className="relative rounded-3xl overflow-hidden border border-gis-border shadow-card bg-slate-100 h-[calc(100vh-250px)] min-h-[500px]">
        <MapContainer
          center={defaultCenter}
          zoom={12}
          className="w-full h-full"
          zoomControl={true}
        >
          {/* Standard OpenStreetMap Leaflet TileLayer */}
          <TileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            maxZoom={19}
          />

          <MapController
            fitBoundsTrigger={fitBoundsTrigger}
            centerDelhiTrigger={centerDelhiTrigger}
            elements={allVisibleElements}
          />

          {/* ── Layer 1: Persistent Hotspot Clusters ────────────────── */}
          {showHotspots &&
            validHotspots.map((hs) => {
              const lat = hs.center_lat ?? hs.latitude ?? hs.lat;
              const lng = hs.center_lng ?? hs.longitude ?? hs.lng;
              const sev = (hs.severity || 'medium').toLowerCase();
              const style = HOTSPOT_STYLES[sev] || HOTSPOT_STYLES.medium;
              const radius = Math.min(380, 80 + (hs.detection_count * 30));

              return (
                <Circle
                  key={`gis-hs-${hs.id}`}
                  center={[lat, lng]}
                  radius={radius}
                  pathOptions={{
                    color: style.stroke,
                    fillColor: style.fill,
                    fillOpacity: 0.22,
                    weight: 2,
                    dashArray: '4 4',
                  }}
                >
                  <Popup>
                    <div className="w-64 font-sans text-xs bg-white text-slate-800">
                      <div className="p-3 bg-amber-500 text-white flex items-center justify-between">
                        <div className="flex items-center gap-1.5 font-extrabold text-sm">
                          <Flame className="w-4 h-4 text-amber-200" />
                          <span>HOTSPOT #{hs.id}</span>
                        </div>
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-black uppercase bg-white/20 text-white">
                          {hs.severity}
                        </span>
                      </div>

                      <div className="p-3 space-y-2 bg-white">
                        <div className="flex items-center justify-between text-[11px]">
                          <span className="text-slate-400 font-semibold uppercase">Cluster Type</span>
                          <span className="font-bold text-slate-800 capitalize">{(hs.event_type || 'pothole').replace('_', ' ')}</span>
                        </div>

                        <div className="bg-amber-50 border border-amber-200 rounded-xl p-2 text-[11px] text-amber-900 font-bold flex items-center gap-1.5">
                          <ShieldAlert className="w-3.5 h-3.5 text-amber-600 shrink-0" />
                          <span>Fleet Corroboration: {hs.detection_count || 1} independent reports</span>
                        </div>

                        <div className="flex items-center justify-between text-[11px]">
                          <span className="text-slate-400 font-semibold uppercase">Maintenance Priority Score</span>
                          <span className="font-extrabold text-red-600 font-mono text-xs">{(hs.priority_score || 5).toFixed(1)} / 10</span>
                        </div>

                        <div className="pt-1.5 border-t border-slate-100 text-[10px] text-slate-400 flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          <span>Last seen: {formatRelativeTime(hs.last_seen || hs.first_seen)}</span>
                        </div>
                      </div>
                    </div>
                  </Popup>
                </Circle>
              );
            })}

          {/* ── Layer 2: Real Detection Events ─────────────────────── */}
          {showEvents &&
            filteredEvents.map((event) => {
              const lat = event.latitude ?? event.lat;
              const lng = event.longitude ?? event.lng;
              const eventId = event.event_id || event.id;
              const type = (event.event_type || '').toLowerCase();
              const sev = (event.severity || 'medium').toLowerCase();
              const isTraffic = ['congestion', 'vehicle_count', 'traffic_snapshot', 'traffic'].includes(type);
              const isCritical = sev === 'critical' || sev === 'high';
              const color = isTraffic ? SEVERITY_COLORS.traffic : (SEVERITY_COLORS[sev] || SEVERITY_COLORS.medium);
              const label = event.repeated_detections > 1 ? `${event.repeated_detections}×` : '';

              const icon = createSvgMarker({
                color,
                label,
                isPulsing: isCritical,
                iconType: isTraffic ? 'traffic' : 'defect',
                size: 26,
              });

              return (
                <Marker key={`gis-evt-${eventId}`} position={[lat, lng]} icon={icon}>
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
                        <div className="h-32 bg-slate-950 overflow-hidden relative">
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
                              <BusIcon className="w-3 h-3 text-blue-600 shrink-0" />
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
                          <button
                            onClick={() => navigate('/events', { state: { selectedEventId: eventId } })}
                            className="w-full bg-slate-800 hover:bg-slate-900 text-white font-bold py-1.5 rounded-xl flex items-center justify-center gap-1 text-[11px] transition-colors cursor-pointer"
                          >
                            <Eye className="w-3 h-3" /> Inspect Event Details
                          </button>
                        </div>
                      </div>
                    </div>
                  </Popup>
                </Marker>
              );
            })}

          {/* ── Layer 3: Active Mobile Bus Fleet Sensors ──────────── */}
          {showBuses &&
            validBuses.map((bus) => {
              const lat = bus.last_lat ?? bus.lat;
              const lng = bus.last_lng ?? bus.lng;
              const busIcon = createBusMarker(bus.id);

              return (
                <Marker key={`gis-bus-${bus.id}`} position={[lat, lng]} icon={busIcon}>
                  <Popup>
                    <div className="w-64 font-sans text-xs bg-white text-slate-800">
                      <div className="p-3 bg-indigo-900 text-white flex items-center justify-between">
                        <div className="flex items-center gap-1.5 font-extrabold text-sm">
                          <BusIcon className="w-4 h-4 text-indigo-300" />
                          <span>{bus.id}</span>
                        </div>
                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-black uppercase ${
                          bus.status === 'Active' ? 'bg-emerald-500/30 text-emerald-200' : 'bg-amber-500/30 text-amber-200'
                        }`}>
                          {bus.status || 'Active'}
                        </span>
                      </div>

                      <div className="p-3 space-y-2 bg-white">
                        <div className="flex items-center justify-between text-[11px]">
                          <span className="text-slate-400 font-semibold uppercase">Assigned Route</span>
                          <span className="font-bold text-slate-800">{bus.route || 'Route 534'}</span>
                        </div>

                        <div className="flex items-center justify-between text-[11px]">
                          <span className="text-slate-400 font-semibold uppercase">Edge AI Camera</span>
                          <span className="font-bold text-emerald-600 flex items-center gap-1">
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                            {bus.camera_status || 'Active'}
                          </span>
                        </div>

                        <div className="flex items-center justify-between text-[11px]">
                          <span className="text-slate-400 font-semibold uppercase">Traffic Reading</span>
                          <span className="font-bold text-slate-700">{bus.last_traffic || 'Moderate'}</span>
                        </div>

                        <div className="pt-1.5 border-t border-slate-100 flex items-center justify-between text-[10px] text-slate-400 font-mono">
                          <span>{lat.toFixed(4)}, {lng.toFixed(4)}</span>
                          <span>{formatRelativeTime(bus.last_seen)}</span>
                        </div>
                      </div>
                    </div>
                  </Popup>
                </Marker>
              );
            })}
        </MapContainer>

        {/* ── Floating Stats Card (Top Left) ──────────────────────── */}
        <div className="absolute top-4 left-4 z-[400] flex flex-col gap-2 pointer-events-none">
          <div className="glass-card rounded-2xl border border-gis-border shadow-float px-3.5 py-2 flex items-center gap-2 text-xs font-extrabold text-slate-700">
            <Navigation className="w-3.5 h-3.5 text-blue-600" />
            <span>{filteredEvents.length} Active Detections</span>
          </div>
          {showHotspots && (
            <div className="glass-card rounded-2xl border border-gis-border shadow-float px-3.5 py-2 flex items-center gap-2 text-xs font-extrabold text-slate-700">
              <Flame className="w-3.5 h-3.5 text-amber-500" />
              <span>{validHotspots.length} Persistent Hotspot Clusters</span>
            </div>
          )}
          {showBuses && (
            <div className="glass-card rounded-2xl border border-gis-border shadow-float px-3.5 py-2 flex items-center gap-2 text-xs font-extrabold text-slate-700">
              <BusIcon className="w-3.5 h-3.5 text-indigo-600" />
              <span>{validBuses.length} Mobile Bus Sensors</span>
            </div>
          )}
        </div>

        {/* ── Floating Legend (Bottom Right) ──────────────────────── */}
        <div className="absolute bottom-5 right-5 z-[400] glass-card rounded-2xl border border-gis-border shadow-float p-3.5 text-xs min-w-[170px]">
          <h4 className="font-extrabold text-slate-800 text-[11px] uppercase tracking-wider mb-2 pb-1.5 border-b border-gis-border">
            GIS Map Legend
          </h4>
          <div className="space-y-1.5 text-slate-600 text-[11px]">
            <div className="flex items-center gap-2">
              <div className="w-3.5 h-3.5 rounded-full bg-red-500 border border-white shadow-sm flex items-center justify-center text-[8px] text-white font-bold">⚠️</div>
              <span className="font-semibold text-slate-700">Pothole (High / Critical)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3.5 h-3.5 rounded-full bg-amber-500 border border-white shadow-sm flex items-center justify-center text-[8px] text-white font-bold">⚠️</div>
              <span className="font-semibold text-slate-700">Road Defect (Medium)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3.5 h-3.5 rounded-full bg-emerald-500 border border-white shadow-sm flex items-center justify-center text-[8px] text-white font-bold">⚠️</div>
              <span className="font-semibold text-slate-700">Minor Defect (Low)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3.5 h-3.5 rounded-full bg-blue-500 border border-white shadow-sm flex items-center justify-center text-[8px] text-white font-bold">🚗</div>
              <span className="font-semibold text-slate-700">Traffic Congestion</span>
            </div>
            {showHotspots && (
              <div className="flex items-center gap-2 pt-1 border-t border-slate-100">
                <div className="w-3.5 h-3.5 rounded-full border-2 border-amber-500/80 bg-amber-500/20" />
                <span className="font-semibold text-slate-700">Persistent Hotspot Cluster</span>
              </div>
            )}
            {showBuses && (
              <div className="flex items-center gap-2">
                <div className="px-1 py-0.5 rounded-full bg-indigo-900 text-white text-[8px] font-bold">🚌 BUS</div>
                <span className="font-semibold text-slate-700">Mobile Bus Sensor</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
