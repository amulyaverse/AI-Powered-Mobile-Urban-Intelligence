/**
 * api.js
 * ------
 * Service layer connecting the frontend to the FastAPI backend.
 *
 * Base URL is read from the VITE_API_BASE_URL environment variable.
 * Default: http://localhost:8000 (local FastAPI dev server)
 *
 * To connect to production:
 *   Set VITE_API_BASE_URL=https://your-backend.railway.app in your .env
 *   or in the Vercel project settings.
 */

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/** Generic fetch wrapper with error handling */
async function apiFetch(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API ${res.status} at ${path}: ${body}`);
  }
  return res.json();
}

// ── System Alerts ─────────────────────────────────────────────────────────────
export const getSystemAlerts = (acknowledged) => {
  const params = acknowledged !== undefined ? `?acknowledged=${acknowledged}` : '';
  return apiFetch(`/api/alerts${params}`);
};

export const acknowledgeAlert = (id) =>
  apiFetch(`/api/alerts/${id}/acknowledge`, {
    method: 'PATCH',
  });

// ── Buses ─────────────────────────────────────────────────────────────────────
export const getBuses = () => apiFetch('/api/buses');

export const getBusById = (id) => apiFetch(`/api/buses/${id}`);

// ── Events ────────────────────────────────────────────────────────────────────
export const getEvents = (filters = {}) => {
  const cleaned = Object.entries(filters).reduce((acc, [k, v]) => {
    if (v !== undefined && v !== null && v !== '') acc[k] = v;
    return acc;
  }, {});
  const params = new URLSearchParams(cleaned).toString();
  return apiFetch(`/api/events${params ? `?${params}` : ''}`);
};

export const getEventById = (id) => apiFetch(`/api/events/${id}`);

export const updateEventStatus = (id, status) =>
  apiFetch(`/api/events/${id}/status`, {
    method: 'PATCH',
    body: JSON.stringify({ status }),
  });

// ── Analytics ─────────────────────────────────────────────────────────────────
export const getKPIMetrics = () => apiFetch('/api/analytics/summary');

export const getTrafficSummary = () => apiFetch('/api/analytics/traffic/summary');

export const getTrafficAnalytics = (hours = 24) =>
  apiFetch(`/api/analytics/traffic?hours=${hours}`);

export const getRoadSummary = () => apiFetch('/api/analytics/road/summary');

export const getRoadConditionAnalytics = (days = 7) =>
  apiFetch(`/api/analytics/road?days=${days}`);

// ── Hotspots ──────────────────────────────────────────────────────────────────
export const getHotspots = (status = 'active') =>
  apiFetch(`/api/hotspots?status=${status}`);

