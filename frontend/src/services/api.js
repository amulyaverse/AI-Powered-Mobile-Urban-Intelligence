/**
 * api.js
 * ------
 * Resilient API service layer connecting the frontend to the FastAPI backend
 * with automatic, graceful fallback to local mock/demo data when the backend
 * is unavailable or in demo mode.
 *
 * Environment variables:
 *   - VITE_API_BASE_URL: Backend URL (e.g. https://your-backend.railway.app)
 *   - VITE_USE_MOCK_DATA: 'true' to force demo mode without attempting network calls
 */

import * as mockData from '../data/mockData';

// ── In-Memory Mock Store (mutations persist during the session) ───────────────
const localStore = {
  buses: JSON.parse(JSON.stringify(mockData.buses)),
  events: JSON.parse(JSON.stringify(mockData.events)),
  kpiMetrics: JSON.parse(JSON.stringify(mockData.kpiMetrics)),
  trafficData: JSON.parse(JSON.stringify(mockData.trafficData)),
  trafficSummary: JSON.parse(JSON.stringify(mockData.trafficSummary)),
  roadConditionData: JSON.parse(JSON.stringify(mockData.roadConditionData)),
  roadSummary: JSON.parse(JSON.stringify(mockData.roadSummary)),
  hotspots: JSON.parse(JSON.stringify(mockData.hotspots)),
  systemAlerts: JSON.parse(JSON.stringify(mockData.systemAlerts)),
};

// ── Configuration ─────────────────────────────────────────────────────────────
const ENV_BASE_URL = import.meta.env.VITE_API_BASE_URL;
const ENV_FORCE_MOCK = import.meta.env.VITE_USE_MOCK_DATA === 'true';

// Resolve default base URL: In dev default to localhost:8000; in production use configured URL or localhost fallback
export const API_BASE_URL = (ENV_BASE_URL || (import.meta.env.DEV ? 'http://localhost:8000' : 'http://localhost:8000')).replace(/\/+$/, '');
const REQUEST_TIMEOUT_MS = 3500;

// ── Reactive Connection State ────────────────────────────────────────────────
let currentMode = ENV_FORCE_MOCK ? 'demo' : 'live'; // 'live' | 'demo'
let connectionStatus = ENV_FORCE_MOCK ? 'demo' : 'unknown'; // 'connected' | 'demo' | 'offline_fallback' | 'unknown'
let lastErrorMessage = '';
const listeners = new Set();

function notifyStatusChange() {
  const state = getConnectionState();
  listeners.forEach((fn) => {
    try {
      fn(state);
    } catch (err) {
      console.error('[API] Listener error:', err);
    }
  });
}

export function getConnectionState() {
  return {
    mode: currentMode,
    status: connectionStatus, // 'connected' | 'demo' | 'offline_fallback' | 'unknown'
    baseUrl: API_BASE_URL,
    isDemo: currentMode === 'demo' || connectionStatus === 'offline_fallback',
    errorMessage: lastErrorMessage,
  };
}

export function subscribeConnectionState(callback) {
  listeners.add(callback);
  callback(getConnectionState());
  return () => listeners.delete(callback);
}

export function setForceDemoMode(enableDemo) {
  currentMode = enableDemo ? 'demo' : 'live';
  connectionStatus = enableDemo ? 'demo' : 'unknown';
  lastErrorMessage = enableDemo ? 'Manual demo mode enabled' : '';
  notifyStatusChange();
}

// ── Robust Core Fetcher with Timeout & Fallback ───────────────────────────────
async function apiFetchWithFallback(path, options = {}, mockFallbackFn) {
  // 1. If explicit demo mode is active, return mock data immediately
  if (currentMode === 'demo') {
    return mockFallbackFn();
  }

  // 2. Attempt live network fetch with AbortController timeout
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  try {
    const url = `${API_BASE_URL}${path}`;
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      signal: controller.signal,
      ...options,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorText = await response.text().catch(() => '');
      throw new Error(`HTTP ${response.status} from ${path}: ${errorText || response.statusText}`);
    }

    const data = await response.json();

    // Mark live connection active
    if (connectionStatus !== 'connected') {
      connectionStatus = 'connected';
      lastErrorMessage = '';
      notifyStatusChange();
    }

    return data;
  } catch (err) {
    clearTimeout(timeoutId);

    const isAbort = err.name === 'AbortError';
    const msg = isAbort
      ? `Request timeout after ${REQUEST_TIMEOUT_MS}ms (${path})`
      : err.message || 'Network connection failed';

    lastErrorMessage = msg;
    console.warn(`[API Gateway] Backend unreachable at ${API_BASE_URL}${path} (${msg}). Falling back to Demo Data.`);

    // Switch status to offline fallback
    if (connectionStatus !== 'offline_fallback') {
      connectionStatus = 'offline_fallback';
      notifyStatusChange();
    }

    // Gracefully return synthetic demo data
    return mockFallbackFn();
  }
}

// ── Normalization Helpers ─────────────────────────────────────────────────────
function normalizeBus(b) {
  if (!b) return b;
  const lat = b.last_lat ?? b.lat ?? 28.5639;
  const lng = b.last_lng ?? b.lng ?? 77.2090;
  const traffic = b.last_traffic ?? b.traffic ?? 'Unknown';
  const camera = b.camera_status ?? b.cameraStatus ?? 'Active';
  const seen = b.last_seen ?? b.lastUpdate ?? new Date().toISOString();
  return {
    ...b,
    id: b.id,
    route: b.route,
    status: b.status || 'Active',
    camera_status: camera,
    cameraStatus: camera,
    last_lat: lat,
    last_lng: lng,
    lat,
    lng,
    last_traffic: traffic,
    traffic,
    last_seen: seen,
    lastUpdate: seen,
  };
}

function normalizeEvent(e) {
  if (!e) return e;
  const eventId = e.event_id || e.id || `EVT_${Math.random().toString(36).substring(2, 9)}`;
  const lat = e.latitude ?? e.lat ?? 28.6139;
  const lng = e.longitude ?? e.lng ?? 77.2090;
  return {
    ...e,
    id: eventId,
    event_id: eventId,
    event_type: (e.event_type || 'pothole').toLowerCase(),
    confidence: typeof e.confidence === 'number' ? e.confidence : 0.85,
    severity: (e.severity || 'medium').toLowerCase(),
    bus_id: e.bus_id || 'BUS_021',
    camera_id: e.camera_id || 'CAM_FRONT',
    latitude: lat,
    longitude: lng,
    lat,
    lng,
    timestamp: e.timestamp || new Date().toISOString(),
    evidence: e.evidence || null,
    status: (e.status || 'new').toLowerCase(),
    repeated_detections: e.repeated_detections ?? 1,
  };
}

function normalizeHotspot(h) {
  if (!h) return h;
  const lat = h.center_lat ?? h.latitude ?? 28.6139;
  const lng = h.center_lng ?? h.longitude ?? 77.2090;
  return {
    ...h,
    id: h.id,
    center_lat: lat,
    center_lng: lng,
    latitude: lat,
    longitude: lng,
    event_type: (h.event_type || 'pothole').toLowerCase(),
    detection_count: h.detection_count ?? h.report_count ?? 1,
    severity: (h.severity || h.max_severity || 'medium').toLowerCase(),
    priority_score: typeof h.priority_score === 'number' ? h.priority_score : 5.0,
    first_seen: h.first_seen || new Date().toISOString(),
    last_seen: h.last_seen || new Date().toISOString(),
    status: (h.status || 'active').toLowerCase(),
    event_ids: h.event_ids || [],
  };
}

function normalizeKPI(m) {
  if (!m) return m;
  return {
    activeBuses: m.activeBuses ?? m.active_buses ?? 0,
    eventsToday: m.eventsToday ?? m.events_today ?? m.total_events ?? 0,
    potholesDetected: m.potholesDetected ?? m.potholes_detected ?? 0,
    trafficHotspots: m.trafficHotspots ?? m.traffic_hotspots ?? 0,
    criticalAlerts: m.criticalAlerts ?? m.critical_alerts ?? 0,
    total_events: m.total_events,
    by_type: m.by_type,
    by_severity: m.by_severity,
  };
}

function normalizeTrafficSummary(s) {
  if (!s) return s;
  return {
    totalVehicles: s.totalVehicles ?? s.total_vehicles ?? 0,
    avgTrafficDensity: s.avgTrafficDensity ?? s.avg_traffic_density ?? 0,
    congestionHotspots: s.congestionHotspots ?? s.congestion_hotspots ?? 0,
    criticalHotspots: s.criticalHotspots ?? s.critical_hotspots ?? 0,
    monitoringFleet: s.monitoringFleet ?? s.monitoring_fleet ?? 0,
    activeCameras: s.activeCameras ?? s.active_cameras ?? 0,
  };
}

function normalizeRoadSummary(s) {
  if (!s) return s;
  return {
    totalPotholes: s.totalPotholes ?? s.total_potholes ?? 0,
    highSeverityIssues: s.highSeverityIssues ?? s.high_severity_issues ?? 0,
    persistentDefects: s.persistentDefects ?? s.persistent_defects ?? 0,
    resolvedDefects: s.resolvedDefects ?? s.resolved_defects ?? 0,
  };
}

function normalizeAlert(a) {
  if (!a) return a;
  return {
    id: a.id,
    severity: (a.severity || 'medium').toLowerCase(),
    message: a.message || 'System Alert',
    source: a.source || 'System',
    details: a.details || '',
    timestamp: a.timestamp || new Date().toISOString(),
    acknowledged: Boolean(a.acknowledged),
  };
}

// ── Health Check ─────────────────────────────────────────────────────────────
export async function checkBackendHealth() {
  if (currentMode === 'demo') {
    return { status: 'demo', isDemo: true };
  }
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 2000);
  try {
    const res = await fetch(`${API_BASE_URL}/health`, { signal: controller.signal });
    clearTimeout(timeoutId);
    if (res.ok) {
      connectionStatus = 'connected';
      notifyStatusChange();
      return { status: 'healthy', isDemo: false };
    }
  } catch {
    clearTimeout(timeoutId);
  }
  connectionStatus = 'offline_fallback';
  notifyStatusChange();
  return { status: 'offline', isDemo: true };
}

// ── System Alerts ─────────────────────────────────────────────────────────────
export const getSystemAlerts = async (acknowledged) => {
  const data = await apiFetchWithFallback(
    `/api/alerts${acknowledged !== undefined ? `?acknowledged=${acknowledged}` : ''}`,
    { method: 'GET' },
    () => {
      let alerts = localStore.systemAlerts;
      if (acknowledged !== undefined) {
        alerts = alerts.filter((a) => a.acknowledged === acknowledged);
      }
      return alerts;
    }
  );
  const rawList = Array.isArray(data) ? data : (data?.items || data?.alerts || []);
  return rawList.map(normalizeAlert);
};

export const acknowledgeAlert = async (id) => {
  const data = await apiFetchWithFallback(
    `/api/alerts/${id}/acknowledge`,
    { method: 'PATCH' },
    () => {
      const idx = localStore.systemAlerts.findIndex((a) => a.id === id);
      if (idx >= 0) {
        localStore.systemAlerts[idx] = { ...localStore.systemAlerts[idx], acknowledged: true };
        return localStore.systemAlerts[idx];
      }
      return { id, acknowledged: true };
    }
  );
  return normalizeAlert(data);
};

// ── Buses ─────────────────────────────────────────────────────────────────────
export const getBuses = async () => {
  const data = await apiFetchWithFallback('/api/buses', { method: 'GET' }, () => localStore.buses);
  const rawList = Array.isArray(data) ? data : (data?.items || data?.buses || []);
  return rawList.map(normalizeBus);
};

export const getBusById = async (id) => {
  const data = await apiFetchWithFallback(`/api/buses/${id}`, { method: 'GET' }, () => {
    const bus = localStore.buses.find((b) => b.id === id);
    if (!bus) throw new Error(`Bus ${id} not found`);
    return bus;
  });
  return normalizeBus(data);
};

// ── Events ────────────────────────────────────────────────────────────────────
export const getEvents = async (filters = {}) => {
  const cleaned = Object.entries(filters).reduce((acc, [k, v]) => {
    if (v !== undefined && v !== null && v !== '' && v !== 'all') acc[k] = v;
    return acc;
  }, {});
  const params = new URLSearchParams(cleaned).toString();

  const data = await apiFetchWithFallback(
    `/api/events${params ? `?${params}` : ''}`,
    { method: 'GET' },
    () => {
      let list = [...localStore.events];
      if (filters.event_type && filters.event_type !== 'all') {
        list = list.filter((e) => e.event_type === filters.event_type);
      }
      if (filters.severity && filters.severity !== 'all') {
        list = list.filter((e) => e.severity === filters.severity);
      }
      if (filters.status && filters.status !== 'all') {
        list = list.filter((e) => e.status === filters.status);
      }
      if (filters.bus_id && filters.bus_id !== 'all') {
        list = list.filter((e) => e.bus_id === filters.bus_id);
      }
      if (filters.search) {
        const q = filters.search.toLowerCase();
        list = list.filter(
          (e) =>
            e.event_id?.toLowerCase().includes(q) ||
            e.bus_id?.toLowerCase().includes(q) ||
            e.event_type?.toLowerCase().includes(q)
        );
      }
      if (filters.limit) {
        list = list.slice(0, Number(filters.limit));
      }
      return list;
    }
  );

  const rawList = Array.isArray(data) ? data : (data?.items || data?.events || []);
  return rawList.map(normalizeEvent);
};

export const getEventById = async (id) => {
  const data = await apiFetchWithFallback(`/api/events/${id}`, { method: 'GET' }, () => {
    const evt = localStore.events.find((e) => e.event_id === id);
    if (!evt) throw new Error(`Event ${id} not found`);
    return evt;
  });
  return normalizeEvent(data);
};

export const updateEventStatus = async (id, status) => {
  const data = await apiFetchWithFallback(
    `/api/events/${id}/status`,
    {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    },
    () => {
      const idx = localStore.events.findIndex((e) => e.event_id === id);
      if (idx >= 0) {
        localStore.events[idx] = { ...localStore.events[idx], status };
        return localStore.events[idx];
      }
      return { event_id: id, status };
    }
  );
  return normalizeEvent(data);
};

// ── Analytics ─────────────────────────────────────────────────────────────────
export const getKPIMetrics = async () => {
  const data = await apiFetchWithFallback('/api/analytics/summary', { method: 'GET' }, () => localStore.kpiMetrics);
  return normalizeKPI(data);
};

export const getTrafficSummary = async () => {
  const data = await apiFetchWithFallback('/api/analytics/traffic/summary', { method: 'GET' }, () => localStore.trafficSummary);
  return normalizeTrafficSummary(data);
};

export const getTrafficAnalytics = async (hours = 24) => {
  const data = await apiFetchWithFallback(
    `/api/analytics/traffic?hours=${hours}`,
    { method: 'GET' },
    () => localStore.trafficData
  );
  return data;
};

export const getRoadSummary = async () => {
  const data = await apiFetchWithFallback('/api/analytics/road/summary', { method: 'GET' }, () => localStore.roadSummary);
  return normalizeRoadSummary(data);
};

export const getRoadConditionAnalytics = async (days = 7) => {
  const data = await apiFetchWithFallback(
    `/api/analytics/road?days=${days}`,
    { method: 'GET' },
    () => localStore.roadConditionData
  );
  return data;
};

// ── Hotspots ──────────────────────────────────────────────────────────────────
export const getHotspots = async (status = 'active') => {
  const data = await apiFetchWithFallback(
    `/api/hotspots?status=${status}`,
    { method: 'GET' },
    () => {
      if (!status || status === 'all') return localStore.hotspots;
      return localStore.hotspots.filter((h) => h.status === status);
    }
  );
  const rawList = Array.isArray(data) ? data : (data?.items || data?.hotspots || []);
  return rawList.map(normalizeHotspot);
};
