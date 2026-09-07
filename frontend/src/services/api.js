/**
 * api.js
 * ------
 * Resilient API service layer connecting the frontend to the FastAPI backend
 * with automatic, graceful fallback to local mock/demo data when the backend
 * is unavailable.
 *
 * Environment variables:
 *   VITE_API_BASE_URL  — Backend URL (e.g. http://localhost:8000)
 *   VITE_USE_MOCK_DATA — Set to 'true' to force demo mode at startup
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

export const API_BASE_URL = (
  ENV_BASE_URL || (import.meta.env.DEV ? 'http://localhost:8000' : 'http://localhost:8000')
).replace(/\/+$/, '');

const REQUEST_TIMEOUT_MS = 3500;

// ── WebSocket URL helper ──────────────────────────────────────────────────────
/**
 * Convert the HTTP base URL to a WebSocket URL.
 * e.g. http://localhost:8000/api/ws/events → ws://localhost:8000/api/ws/events
 */
export function getWsUrl(path) {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  if (!ENV_BASE_URL && typeof window !== 'undefined' && window.location) {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${protocol}//${window.location.host}${normalizedPath}`;
  }
  const base = API_BASE_URL.replace(/^http/, 'ws');
  return `${base}${normalizedPath}`;
}

// ── Reactive Connection State & Auto-Reconnection Polling ─────────────────────
let currentMode        = ENV_FORCE_MOCK ? 'demo' : 'live'; // 'live' | 'demo'
let connectionStatus   = ENV_FORCE_MOCK ? 'demo' : 'unknown'; // 'connected' | 'demo' | 'offline_fallback' | 'unknown'
let lastErrorMessage   = '';
let healthPollInterval = null;
const listeners        = new Set();

function notifyStatusChange() {
  const state = getConnectionState();
  listeners.forEach((fn) => {
    try { fn(state); } catch (e) { console.error('[API] Listener error:', e); }
  });
}

export function getConnectionState() {
  return {
    mode: currentMode,
    status: connectionStatus,
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
  if (enableDemo) {
    stopHealthPolling();
  } else {
    checkBackendHealth();
  }
  notifyStatusChange();
}

function startHealthPolling() {
  if (healthPollInterval || currentMode === 'demo') return;
  // Poll every 10s to detect when backend comes back online
  healthPollInterval = setInterval(async () => {
    if (connectionStatus === 'offline_fallback' || connectionStatus === 'unknown') {
      await checkBackendHealth();
    }
  }, 10000);
}

function stopHealthPolling() {
  if (healthPollInterval) {
    clearInterval(healthPollInterval);
    healthPollInterval = null;
  }
}

// ── Core Fetcher with Strict Live Mode & Fallback ─────────────────────────────
async function apiFetchWithFallback(path, options = {}, mockFallbackFn) {
  // 1. Explicit user demo mode → always return mock data
  if (currentMode === 'demo') {
    return mockFallbackFn ? mockFallbackFn() : null;
  }

  // 2. If already offline, provide instant mock data without waiting for network timeout
  if (connectionStatus === 'offline_fallback' && mockFallbackFn) {
    startHealthPolling();
    return mockFallbackFn();
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  try {
    const url = `${API_BASE_URL}${path}`;
    const response = await fetch(url, {
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      signal: controller.signal,
      ...options,
    });
    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorText = await response.text().catch(() => '');
      const err = new Error(`HTTP ${response.status} from ${path}: ${errorText || response.statusText}`);
      err.isHttpError = true;
      err.status = response.status;
      throw err;
    }

    const data = await response.json();

    // Mark as connected and stop polling
    if (connectionStatus !== 'connected') {
      connectionStatus = 'connected';
      lastErrorMessage = '';
      stopHealthPolling();
      notifyStatusChange();
    }
    return data;

  } catch (err) {
    clearTimeout(timeoutId);

    // If it's an HTTP error (400, 404, 500), backend is ALIVE and reachable!
    if (err.isHttpError) {
      if (connectionStatus !== 'connected') {
        connectionStatus = 'connected';
        stopHealthPolling();
        notifyStatusChange();
      }
      console.warn(`[API] Server responded with error for ${path}:`, err.message);
      // In live mode, return empty/safe defaults rather than synthetic mock data
      return Array.isArray(mockFallbackFn?.()) ? [] : null;
    }

    // Genuine network / unreachable failure (connection refused, timeout, DNS error)
    const msg = err.name === 'AbortError'
      ? `Request timeout after ${REQUEST_TIMEOUT_MS}ms (${path})`
      : err.message || 'Network connection failed';

    lastErrorMessage = msg;
    console.warn(`[API] Backend unreachable (${msg}) — falling back to offline demo data.`);

    if (connectionStatus !== 'offline_fallback') {
      connectionStatus = 'offline_fallback';
      startHealthPolling();
      notifyStatusChange();
    }

    // Return mock data so the UI never displays an infinite spinner
    return mockFallbackFn ? mockFallbackFn() : null;
  }
}

// ── Health Check Probe ────────────────────────────────────────────────────────
export async function checkBackendHealth() {
  if (currentMode === 'demo') return { status: 'demo', isDemo: true };

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 2000);

  try {
    const res = await fetch(`${API_BASE_URL}/health`, { signal: controller.signal });
    clearTimeout(timeoutId);

    if (res.ok) {
      const wasOffline = connectionStatus !== 'connected';
      connectionStatus = 'connected';
      lastErrorMessage = '';
      stopHealthPolling();
      if (wasOffline) notifyStatusChange();
      return { status: 'healthy', isDemo: false };
    }
  } catch (err) {
    clearTimeout(timeoutId);
  }

  const wasOnline = connectionStatus === 'connected';
  connectionStatus = 'offline_fallback';
  startHealthPolling();
  if (wasOnline || connectionStatus !== 'offline_fallback') {
    notifyStatusChange();
  }
  return { status: 'offline', isDemo: true };
}

// Perform instant probe on module initialization
if (typeof window !== 'undefined' && !ENV_FORCE_MOCK) {
  setTimeout(() => { checkBackendHealth(); }, 100);
}

// ── Normalisation Helpers ─────────────────────────────────────────────────────
function normalizeBus(b) {
  if (!b) return b;
  const lat = b.last_lat ?? b.lat ?? 28.5639;
  const lng = b.last_lng ?? b.lng ?? 77.2090;
  const traffic = b.last_traffic ?? b.traffic ?? 'Unknown';
  const camera = b.camera_status ?? b.cameraStatus ?? 'Active';
  const seen = b.last_seen ?? b.lastUpdate ?? new Date().toISOString();
  return {
    ...b, id: b.id, route: b.route, status: b.status || 'Active',
    camera_status: camera, cameraStatus: camera,
    last_lat: lat, last_lng: lng, lat, lng,
    last_traffic: traffic, traffic, last_seen: seen, lastUpdate: seen
  };
}

function normalizeEvent(e) {
  if (!e) return e;
  const eventId = e.event_id || e.id || `EVT_${Math.random().toString(36).substring(2, 9)}`;
  const lat = e.latitude ?? e.lat ?? 28.6139;
  const lng = e.longitude ?? e.lng ?? 77.2090;
  return {
    ...e, id: eventId, event_id: eventId,
    event_type: (e.event_type || 'pothole').toLowerCase(),
    confidence: typeof e.confidence === 'number' ? e.confidence : 0.85,
    severity: (e.severity || 'medium').toLowerCase(),
    bus_id: e.bus_id || 'BUS_021', camera_id: e.camera_id || 'CAM_FRONT',
    latitude: lat, longitude: lng, lat, lng,
    timestamp: e.timestamp || new Date().toISOString(),
    evidence: e.evidence || null,
    status: (e.status || 'new').toLowerCase(),
    repeated_detections: e.repeated_detections ?? 1
  };
}

function normalizeHotspot(h) {
  if (!h) return h;
  const lat = h.center_lat ?? h.latitude ?? 28.6139;
  const lng = h.center_lng ?? h.longitude ?? 77.2090;
  return {
    ...h, id: h.id, center_lat: lat, center_lng: lng, latitude: lat, longitude: lng,
    event_type: (h.event_type || 'pothole').toLowerCase(),
    detection_count: h.detection_count ?? h.report_count ?? 1,
    severity: (h.severity || h.max_severity || 'medium').toLowerCase(),
    priority_score: typeof h.priority_score === 'number' ? h.priority_score : 5.0,
    first_seen: h.first_seen || new Date().toISOString(),
    last_seen: h.last_seen || new Date().toISOString(),
    status: (h.status || 'active').toLowerCase(),
    event_ids: h.event_ids || []
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
    total_events: m.total_events, by_type: m.by_type, by_severity: m.by_severity
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
    activeCameras: s.activeCameras ?? s.active_cameras ?? 0
  };
}

function normalizeRoadSummary(s) {
  if (!s) return s;
  return {
    totalPotholes: s.totalPotholes ?? s.total_potholes ?? 0,
    highSeverityIssues: s.highSeverityIssues ?? s.high_severity_issues ?? 0,
    persistentDefects: s.persistentDefects ?? s.persistent_defects ?? 0,
    resolvedDefects: s.resolvedDefects ?? s.resolved_defects ?? 0
  };
}

function normalizeAlert(a) {
  if (!a) return a;
  return {
    id: a.id, severity: (a.severity || 'medium').toLowerCase(),
    message: a.message || 'System Alert', source: a.source || 'System',
    details: a.details || '', timestamp: a.timestamp || new Date().toISOString(),
    acknowledged: Boolean(a.acknowledged)
  };
}

// ── System Alerts ─────────────────────────────────────────────────────────────
export const getSystemAlerts = async (acknowledged) => {
  const data = await apiFetchWithFallback(
    `/api/alerts${acknowledged !== undefined ? `?acknowledged=${acknowledged}` : ''}`,
    { method: 'GET' },
    () => {
      let alerts = localStore.systemAlerts;
      if (acknowledged !== undefined) alerts = alerts.filter((a) => a.acknowledged === acknowledged);
      return alerts;
    }
  );
  const rawList = Array.isArray(data) ? data : (data?.items || data?.alerts || []);
  return rawList.map(normalizeAlert);
};

export const acknowledgeAlert = async (id) => {
  const data = await apiFetchWithFallback(
    `/api/alerts/${id}/acknowledge`, { method: 'PATCH' },
    () => {
      const idx = localStore.systemAlerts.findIndex((a) => a.id === id);
      if (idx >= 0) { localStore.systemAlerts[idx] = { ...localStore.systemAlerts[idx], acknowledged: true }; return localStore.systemAlerts[idx]; }
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

/**
 * Create a new bus in the fleet.
 * NOTE: This is a WRITE operation and REQUIRES the live backend.
 * It does NOT fall back to demo data — it throws a clear error in demo/offline mode
 * so the user knows the backend must be running.
 */
export const createBus = async (data) => {
  if (currentMode === 'demo' || connectionStatus === 'offline_fallback') {
    throw new Error(
      'Fleet Management CRUD requires the live backend. ' +
      'Please start the FastAPI server (cd backend && uvicorn app.main:app --reload --port 8000) ' +
      'and switch to "Live API" mode in Platform Settings.'
    );
  }
  const url = `${API_BASE_URL}/api/buses`;
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({}));
    const detail = errorBody?.detail || `HTTP ${response.status}`;
    throw new Error(detail);
  }
  const created = await response.json();
  return normalizeBus(created);
};

/**
 * Update a bus's editable fields (route, status, camera_status).
 * WRITE operation — requires live backend.
 */
export const updateBus = async (id, data) => {
  if (currentMode === 'demo' || connectionStatus === 'offline_fallback') {
    throw new Error(
      'Fleet Management CRUD requires the live backend. ' +
      'Please start the FastAPI server and switch to "Live API" mode in Platform Settings.'
    );
  }
  const url = `${API_BASE_URL}/api/buses/${id}`;
  const response = await fetch(url, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({}));
    const detail = errorBody?.detail || `HTTP ${response.status}`;
    throw new Error(detail);
  }
  const updated = await response.json();
  return normalizeBus(updated);
};

/**
 * Delete a bus from the fleet.
 * WRITE operation — requires live backend.
 * Returns 409 conflict if the bus has associated events.
 */
export const deleteBus = async (id) => {
  if (currentMode === 'demo' || connectionStatus === 'offline_fallback') {
    throw new Error(
      'Fleet Management CRUD requires the live backend. ' +
      'Please start the FastAPI server and switch to "Live API" mode in Platform Settings.'
    );
  }
  const url = `${API_BASE_URL}/api/buses/${id}`;
  const response = await fetch(url, {
    method: 'DELETE',
    headers: { Accept: 'application/json' },
  });
  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({}));
    const detail = errorBody?.detail || `HTTP ${response.status}`;
    throw new Error(detail);
  }
  // 204 No Content — no body to parse
};

// ── Events ────────────────────────────────────────────────────────────────────
export const getEvents = async (filters = {}) => {
  const cleaned = Object.entries(filters).reduce((acc, [k, v]) => {
    if (v !== undefined && v !== null && v !== '' && v !== 'all') acc[k] = v;
    return acc;
  }, {});
  const params = new URLSearchParams(cleaned).toString();

  const data = await apiFetchWithFallback(
    `/api/events${params ? `?${params}` : ''}`, { method: 'GET' },
    () => {
      let list = [...localStore.events];
      if (filters.event_type && filters.event_type !== 'all') list = list.filter((e) => e.event_type === filters.event_type);
      if (filters.severity && filters.severity !== 'all') list = list.filter((e) => e.severity === filters.severity);
      if (filters.status && filters.status !== 'all') list = list.filter((e) => e.status === filters.status);
      if (filters.bus_id && filters.bus_id !== 'all') list = list.filter((e) => e.bus_id === filters.bus_id);
      if (filters.search) {
        const q = filters.search.toLowerCase();
        list = list.filter((e) => e.event_id?.toLowerCase().includes(q) || e.bus_id?.toLowerCase().includes(q) || e.event_type?.toLowerCase().includes(q));
      }
      if (filters.limit) list = list.slice(0, Number(filters.limit));
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
    `/api/events/${id}/status`, { method: 'PATCH', body: JSON.stringify({ status }) },
    () => {
      const idx = localStore.events.findIndex((e) => e.event_id === id);
      if (idx >= 0) { localStore.events[idx] = { ...localStore.events[idx], status }; return localStore.events[idx]; }
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
  return await apiFetchWithFallback(`/api/analytics/traffic?hours=${hours}`, { method: 'GET' }, () => localStore.trafficData);
};

export const getRoadSummary = async () => {
  const data = await apiFetchWithFallback('/api/analytics/road/summary', { method: 'GET' }, () => localStore.roadSummary);
  return normalizeRoadSummary(data);
};

export const getRoadConditionAnalytics = async (days = 7) => {
  return await apiFetchWithFallback(`/api/analytics/road?days=${days}`, { method: 'GET' }, () => localStore.roadConditionData);
};

// ── Hotspots ──────────────────────────────────────────────────────────────────
export const getHotspots = async (status = 'active') => {
  const data = await apiFetchWithFallback(
    `/api/hotspots?status=${status}`, { method: 'GET' },
    () => (!status || status === 'all') ? localStore.hotspots : localStore.hotspots.filter((h) => h.status === status)
  );
  const rawList = Array.isArray(data) ? data : (data?.items || data?.hotspots || []);
  return rawList.map(normalizeHotspot);
};

// ── PR #37 Videos & Pothole Telemetry ─────────────────────────────────────────
export const getSampleVideos = async () => {
  return await apiFetchWithFallback('/api/videos/samples', { method: 'GET' }, () => [
    {
      id: 'cityRoad_potHoles.mp4',
      title: 'City Road Potholes (Front Angle)',
      filename: 'cityRoad_potHoles.mp4',
      category: 'road_defect',
      description: 'Urban street footage with road surface potholes and asphalt defects (PR #37).',
      recommended_mode: 'pothole',
      source: 'Pothole_Road_Condition_Model',
      available: true,
      stream_url: '/api/videos/stream/cityRoad_potHoles.mp4',
    },
    {
      id: 'cityRoad_potHoles-side.mp4',
      title: 'City Road Potholes (Side View)',
      filename: 'cityRoad_potHoles-side.mp4',
      category: 'road_defect',
      description: 'Angled urban perspective capturing road defect edges and depth contours.',
      recommended_mode: 'pothole',
      source: 'Pothole_Road_Condition_Model',
      available: true,
      stream_url: '/api/videos/stream/cityRoad_potHoles-side.mp4',
    },
    {
      id: 'ruralRoad_potHoles.mp4',
      title: 'Rural Road Severe Defects',
      filename: 'ruralRoad_potHoles.mp4',
      category: 'road_defect',
      description: 'Unpaved and broken asphalt road sections showing high-severity road damage.',
      recommended_mode: 'pothole',
      source: 'Pothole_Road_Condition_Model',
      available: true,
      stream_url: '/api/videos/stream/ruralRoad_potHoles.mp4',
    },
  ]);
};

export const seedPr37Events = async () => {
  return await apiFetchWithFallback('/api/events/seed-pr37', { method: 'POST' }, () => ({
    status: 'ok',
    message: 'PR 37 demo events loaded.',
    events_seeded: 50,
  }));
};
