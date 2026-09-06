/**
 * useEventWebSocket.js
 * ---------------------
 * Custom React hook that subscribes to the backend's live event feed.
 *
 * The backend pushes JSON event payloads over WS /api/ws/events whenever
 * a bus camera produces an accepted AI detection. This hook manages the
 * full WebSocket lifecycle:
 *   - Connect on mount, reconnect with exponential back-off on failure.
 *   - Parse incoming JSON messages and accumulate them in a local history.
 *   - Send a keep-alive ping every 25 s to prevent proxy timeouts.
 *   - Clean up on unmount.
 *
 * Returns:
 *   isConnected   {boolean}  — WebSocket is currently open
 *   latestEvent   {object}   — most recent event payload (null if none)
 *   eventHistory  {array}    — last MAX_HISTORY events, newest-first
 *   wsStatus      {string}   — 'connecting' | 'connected' | 'disconnected' | 'error'
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { getWsUrl, getEvents } from '../services/api';

const MAX_HISTORY = 50;
const PING_INTERVAL_MS = 25_000;
const INITIAL_RECONNECT_MS = 1_500;
const MAX_RECONNECT_MS = 30_000;

export function useEventWebSocket() {
  const [isConnected, setIsConnected] = useState(false);
  const [latestEvent, setLatestEvent] = useState(null);
  const [eventHistory, setEventHistory] = useState([]);
  const [wsStatus, setWsStatus] = useState('connecting');

  const wsRef = useRef(null);
  const pingTimerRef = useRef(null);
  const reconnectTimerRef = useRef(null);
  const reconnectDelayRef = useRef(INITIAL_RECONNECT_MS);
  const unmountedRef = useRef(false);

  // ── 1. Fetch initial recent events on mount ─────────────────────────────────
  useEffect(() => {
    let cancelled = false;
    getEvents({ limit: 30 })
      .then((initial) => {
        if (cancelled || !Array.isArray(initial) || initial.length === 0) return;
        setEventHistory((prev) => {
          const map = new Map();
          initial.forEach((e) => { if (e.event_id) map.set(e.event_id, e); });
          prev.forEach((e) => { if (e.event_id) map.set(e.event_id, e); });
          const merged = Array.from(map.values());
          merged.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
          return merged.slice(0, MAX_HISTORY);
        });
        setLatestEvent((prev) => prev || initial[0]);
      })
      .catch((err) => console.warn('[EventWS] Failed to fetch initial events:', err));

    return () => { cancelled = true; };
  }, []);

  // ── 2. Fallback polling every 5s to guarantee fresh data ────────────────────
  useEffect(() => {
    const poller = setInterval(async () => {
      if (unmountedRef.current) return;
      try {
        const fresh = await getEvents({ limit: 30 });
        if (Array.isArray(fresh) && fresh.length > 0) {
          setEventHistory((prev) => {
            const map = new Map();
            fresh.forEach((e) => { if (e.event_id) map.set(e.event_id, e); });
            prev.forEach((e) => { if (e.event_id) map.set(e.event_id, e); });
            const merged = Array.from(map.values());
            merged.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
            return merged.slice(0, MAX_HISTORY);
          });
        }
      } catch {
        /* ignore polling errors */
      }
    }, 5000);

    return () => clearInterval(poller);
  }, []);

  // ── 3. WebSocket Real-Time Connection ───────────────────────────────────────
  const connect = useCallback(() => {
    if (unmountedRef.current) return;

    setWsStatus('connecting');

    let ws;
    try {
      ws = new WebSocket(getWsUrl('/api/ws/events'));
    } catch (err) {
      console.error('[EventWS] Failed to construct WebSocket:', err);
      setWsStatus('error');
      return;
    }

    wsRef.current = ws;

    ws.onopen = () => {
      if (unmountedRef.current) return ws.close();
      setIsConnected(true);
      setWsStatus('connected');
      reconnectDelayRef.current = INITIAL_RECONNECT_MS; // reset back-off

      // Keep-alive ping
      pingTimerRef.current = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send('ping');
        }
      }, PING_INTERVAL_MS);
    };

    ws.onmessage = (e) => {
      if (unmountedRef.current) return;
      if (e.data === 'pong') return; // ignore keep-alive responses

      try {
        const event = JSON.parse(e.data);
        if (!event || !event.event_id) return;

        setLatestEvent(event);
        setEventHistory((prev) => {
          const filtered = prev.filter((item) => item.event_id !== event.event_id);
          return [event, ...filtered].slice(0, MAX_HISTORY);
        });
      } catch (err) {
        console.warn('[EventWS] Failed to parse message:', e.data, err);
      }
    };

    ws.onclose = () => {
      if (unmountedRef.current) return;
      setIsConnected(false);
      setWsStatus('disconnected');
      clearInterval(pingTimerRef.current);

      // Exponential back-off reconnect
      const delay = reconnectDelayRef.current;
      reconnectDelayRef.current = Math.min(delay * 2, MAX_RECONNECT_MS);
      console.info(`[EventWS] Disconnected. Reconnecting in ${delay}ms...`);
      reconnectTimerRef.current = setTimeout(connect, delay);
    };

    ws.onerror = (err) => {
      if (unmountedRef.current) return;
      console.error('[EventWS] WebSocket error:', err);
      setWsStatus('error');
    };
  }, []);

  useEffect(() => {
    unmountedRef.current = false;
    connect();

    return () => {
      unmountedRef.current = true;
      clearInterval(pingTimerRef.current);
      clearTimeout(reconnectTimerRef.current);
      if (wsRef.current) {
        wsRef.current.onclose = null;
        wsRef.current.close();
      }
    };
  }, [connect]);

  return { isConnected, latestEvent, eventHistory, wsStatus };
}
