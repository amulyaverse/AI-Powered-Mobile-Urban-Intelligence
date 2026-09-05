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
export const getSystemAlerts = (acknowledged) =>
  apiFetchWithFallback(
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

export const acknowledgeAlert = (id) =>
  apiFetchWithFallback(
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

// ── Buses ─────────────────────────────────────────────────────────────────────
export const getBuses = () =>
  apiFetchWithFallback('/api/buses', { method: 'GET' }, () => localStore.buses);

export const getBusById = (id) =>
  apiFetchWithFallback(`/api/buses/${id}`, { method: 'GET' }, () => {
    const bus = localStore.buses.find((b) => b.id === id);
    if (!bus) throw new Error(`Bus ${id} not found`);
    return bus;
  });

// ── Events ────────────────────────────────────────────────────────────────────
export const getEvents = (filters = {}) => {
  const cleaned = Object.entries(filters).reduce((acc, [k, v]) => {
    if (v !== undefined && v !== null && v !== '' && v !== 'all') acc[k] = v;
    return acc;
  }, {});
  const params = new URLSearchParams(cleaned).toString();

  return apiFetchWithFallback(
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
};

export const getEventById = (id) =>
  apiFetchWithFallback(`/api/events/${id}`, { method: 'GET' }, () => {
    const evt = localStore.events.find((e) => e.event_id === id);
    if (!evt) throw new Error(`Event ${id} not found`);
    return evt;
  });

export const updateEventStatus = (id, status) =>
  apiFetchWithFallback(
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

// ── Analytics ─────────────────────────────────────────────────────────────────
export const getKPIMetrics = () =>
  apiFetchWithFallback('/api/analytics/summary', { method: 'GET' }, () => localStore.kpiMetrics);

export const getTrafficSummary = () =>
  apiFetchWithFallback('/api/analytics/traffic/summary', { method: 'GET' }, () => localStore.trafficSummary);

export const getTrafficAnalytics = (hours = 24) =>
  apiFetchWithFallback(
    `/api/analytics/traffic?hours=${hours}`,
    { method: 'GET' },
    () => localStore.trafficData
  );

export const getRoadSummary = () =>
  apiFetchWithFallback('/api/analytics/road/summary', { method: 'GET' }, () => localStore.roadSummary);

export const getRoadConditionAnalytics = (days = 7) =>
  apiFetchWithFallback(
    `/api/analytics/road?days=${days}`,
    { method: 'GET' },
    () => localStore.roadConditionData
  );

// ── Hotspots ──────────────────────────────────────────────────────────────────
export const getHotspots = (status = 'active') =>
  apiFetchWithFallback(
    `/api/hotspots?status=${status}`,
    { method: 'GET' },
    () => {
      if (!status || status === 'all') return localStore.hotspots;
      return localStore.hotspots.filter((h) => h.status === status);
    }
  );
