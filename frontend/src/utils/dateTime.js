/**
 * dateTime.js
 * -----------
 * Centralised utility for robust date parsing, timezone handling,
 * and formatting across the Urban Intelligence platform.
 *
 * Prevents the classic UTC/local timezone skew where SQLite timestamps
 * without 'Z' (e.g. '2026-09-06 16:54:11') get parsed as local time
 * rather than UTC, causing several hours of discrepancy.
 */

import { format, formatDistanceToNow, isValid } from 'date-fns';

/**
 * Safely parses any date string, number, or Date instance into a valid Date object.
 * Assumes naive strings from backend / SQLite represent UTC.
 */
export function parseApiDate(dateStr) {
  if (!dateStr) return null;
  if (dateStr instanceof Date) return isNaN(dateStr.getTime()) ? null : dateStr;

  let str = String(dateStr).trim();
  if (!str) return null;

  // Numeric epoch timestamp (seconds or milliseconds)
  if (/^\d+(\.\d+)?$/.test(str)) {
    const num = parseFloat(str);
    const d = new Date(num > 1e11 ? num : num * 1000);
    return isNaN(d.getTime()) ? null : d;
  }

  // Replace space with 'T' (e.g., '2026-09-06 16:54:11' -> '2026-09-06T16:54:11')
  if (str.includes(' ') && !str.includes('T')) {
    str = str.replace(' ', 'T');
  }

  // If no timezone offset (+/-HH:MM or Z) is present, treat as UTC by appending 'Z'
  if (!str.endsWith('Z') && !/[+-]\d{2}(:\d{2})?$/.test(str)) {
    str = str + 'Z';
  }

  const d = new Date(str);
  return isNaN(d.getTime()) ? null : d;
}

/**
 * Formats date into readable local string (e.g. '06 Sep 2026, 22:31:15').
 */
export function formatDateTime(dateStr, pattern = 'dd MMM yyyy, HH:mm:ss') {
  const d = parseApiDate(dateStr);
  if (!d || !isValid(d)) return '—';
  try {
    return format(d, pattern);
  } catch {
    return '—';
  }
}

/**
 * Formats time only (e.g. '22:31:15').
 */
export function formatTimeOnly(dateStr, pattern = 'HH:mm:ss') {
  return formatDateTime(dateStr, pattern);
}

/**
 * Returns user-friendly relative time (e.g. 'Just now', '2 minutes ago').
 * Automatically guards against server/client clock skew within 30s.
 */
export function formatRelativeTime(dateStr) {
  const d = parseApiDate(dateStr);
  if (!d || !isValid(d)) return 'Just now';

  const diffMs = Date.now() - d.getTime();

  // If event happened in the last 45 seconds or slight future clock skew
  if (diffMs < 45_000 && diffMs > -30_000) {
    return 'Just now';
  }
  if (diffMs >= 45_000 && diffMs < 90_000) {
    return '1m ago';
  }

  try {
    return formatDistanceToNow(d, { addSuffix: true });
  } catch {
    return 'Just now';
  }
}
