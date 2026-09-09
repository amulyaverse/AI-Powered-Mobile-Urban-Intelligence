import React, { useEffect, useState, useCallback } from 'react';
import { useLocation } from 'react-router-dom';
import { formatDateTime, formatRelativeTime } from '../utils/dateTime';
import { Filter, Search, Eye, AlertTriangle, X, Maximize2, Minimize2, Radio, Clock } from 'lucide-react';
import { LoadingState, ErrorState } from '../components/PageStatusState';
import CapturedEvidenceViewer, { getEvidenceFrameUrl } from '../components/CapturedEvidenceViewer';
import { useEventWebSocket } from '../hooks/useEventWebSocket';
import { getEvents, updateEventStatus } from '../services/api';

export default function EventPage() {
  const location = useLocation();
  const [events, setEvents] = useState([]);
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [isEvidenceExpanded, setIsEvidenceExpanded] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [filterType, setFilterType] = useState('all');
  const [filterSeverity, setFilterSeverity] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const { latestEvent, isConnected: isWsConnected } = useEventWebSocket();

  // Dynamically prepend incoming live edge detections & handle real-time status changes
  useEffect(() => {
    if (!latestEvent?.event_id) return;

    if (latestEvent.type === 'status_update') {
      setEvents((prev) =>
        prev.map((e) => (e.event_id === latestEvent.event_id ? { ...e, status: latestEvent.status } : e))
      );
      setSelectedEvent((prev) =>
        prev?.event_id === latestEvent.event_id ? { ...prev, status: latestEvent.status } : prev
      );
      return;
    }

    const normEventType = (latestEvent.event_type || '').toLowerCase();
    const normSeverity = (latestEvent.severity || '').toLowerCase();
    const normStatus = (latestEvent.status || 'new').toLowerCase();

    // Filter matching guard
    if (filterType !== 'all') {
      if (filterType === 'congestion') {
        if (!['congestion', 'vehicle_count', 'traffic_snapshot', 'traffic'].includes(normEventType)) return;
      } else if (filterType === 'road_defect') {
        if (!['road_defect', 'crack'].includes(normEventType)) return;
      } else if (normEventType !== filterType) {
        return;
      }
    }
    if (filterSeverity !== 'all') {
      const isSevMatch = (filterSeverity === 'critical')
        ? (normSeverity === 'critical' || normSeverity === 'very high' || normSeverity === 'very_high')
        : (normSeverity === filterSeverity);
      if (!isSevMatch) return;
    }
    if (filterStatus !== 'all' && normStatus !== filterStatus) return;
    if (searchTerm.trim()) {
      const term = searchTerm.toLowerCase();
      const matches =
        latestEvent.event_id?.toLowerCase().includes(term) ||
        latestEvent.bus_id?.toLowerCase().includes(term) ||
        normEventType.includes(term);
      if (!matches) return;
    }

    const normalizedIncoming = {
      ...latestEvent,
      id: latestEvent.event_id,
      event_type: normEventType,
      severity: normSeverity,
      status: normStatus,
      timestamp: latestEvent.timestamp || new Date().toISOString(),
    };

    setEvents((prev) => {
      const exists = prev.some((e) => e.event_id === normalizedIncoming.event_id);
      if (exists) {
        return prev.map((e) => (e.event_id === normalizedIncoming.event_id ? { ...e, ...normalizedIncoming } : e));
      }
      return [normalizedIncoming, ...prev];
    });
  }, [latestEvent, filterType, filterSeverity, filterStatus, searchTerm]);

  const loadData = useCallback(async (isInitial = false) => {
    if (isInitial) setLoading(true);
    try {
      // Load all telemetry events (up to 300 events)
      const data = await getEvents({ limit: 300 });
      const safeEvents = Array.isArray(data) ? data : [];
      setEvents((prev) => {
        const map = new Map();
        safeEvents.forEach((e) => { if (e.event_id) map.set(e.event_id, e); });
        // Preserve any live prepended edge events
        prev.forEach((e) => {
          if (e.event_id && !map.has(e.event_id) && e._isLive) {
            map.set(e.event_id, e);
          }
        });
        const merged = Array.from(map.values());
        merged.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
        return merged;
      });
      setError(null);

      // Auto-open if selectedEventId was passed via route state
      if (location.state?.selectedEventId) {
        const target = safeEvents.find((e) => e.event_id === location.state.selectedEventId);
        if (target) setSelectedEvent(target);
      }
    } catch (err) {
      console.error('[EventPage] Failed to load events:', err);
      if (isInitial) setError(err.message || 'Failed to load event list.');
    } finally {
      if (isInitial) setLoading(false);
    }
  }, [location.state]);

  useEffect(() => {
    loadData(true);
  }, [loadData]);

  // When navigated with a selectedEventId from AlertPanel or Overview, sync search filter
  useEffect(() => {
    if (location.state?.selectedEventId) {
      setSearchTerm(location.state.selectedEventId);
    }
  }, [location.state?.selectedEventId]);

  // Periodic background sync every 6s to keep real-time list fresh
  useEffect(() => {
    const poller = setInterval(() => {
      loadData(false);
    }, 6000);
    return () => clearInterval(poller);
  }, [loadData]);

  // Instant responsive client-side filtering across search term, type, severity, and status
  const filteredEvents = React.useMemo(() => {
    return events.filter((event) => {
      // 1. Search term match (event_id, bus_id, event_type, severity, status)
      if (searchTerm.trim()) {
        const term = searchTerm.trim().toLowerCase();
        const idMatch = (event.event_id || '').toLowerCase().includes(term);
        const busMatch = (event.bus_id || '').toLowerCase().includes(term);
        const typeMatch = (event.event_type || '').toLowerCase().includes(term);
        const sevMatch = (event.severity || '').toLowerCase().includes(term);
        const statusMatch = (event.status || '').toLowerCase().includes(term);
        if (!idMatch && !busMatch && !typeMatch && !sevMatch && !statusMatch) return false;
      }

      // 2. Event type filter
      if (filterType !== 'all') {
        const evtType = (event.event_type || '').toLowerCase();
        if (filterType === 'congestion') {
          if (!['congestion', 'vehicle_count', 'traffic_snapshot', 'traffic'].includes(evtType)) return false;
        } else if (filterType === 'road_defect') {
          if (!['road_defect', 'crack'].includes(evtType)) return false;
        } else if (evtType !== filterType.toLowerCase()) {
          return false;
        }
      }

      // 3. Severity filter
      if (filterSeverity !== 'all') {
        const sev = (event.severity || '').toLowerCase();
        if (filterSeverity === 'critical') {
          if (sev !== 'critical' && sev !== 'very high' && sev !== 'very_high') return false;
        } else if (sev !== filterSeverity.toLowerCase()) {
          return false;
        }
      }

      // 4. Status filter
      if (filterStatus !== 'all') {
        const st = (event.status || 'new').toLowerCase();
        if (st !== filterStatus.toLowerCase()) return false;
      }

      return true;
    });
  }, [events, searchTerm, filterType, filterSeverity, filterStatus]);

  // Quick filter counts
  const counts = React.useMemo(() => {
    let potholes = 0;
    let defects = 0;
    let congestion = 0;
    let critical = 0;
    let high = 0;
    events.forEach((e) => {
      const t = (e.event_type || '').toLowerCase();
      const s = (e.severity || '').toLowerCase();
      if (t === 'pothole') potholes += 1;
      if (t === 'road_defect' || t === 'crack') defects += 1;
      if (t === 'congestion' || t === 'vehicle_count' || t === 'traffic_snapshot' || t === 'traffic') congestion += 1;
      if (s === 'critical' || s === 'very high' || s === 'very_high') critical += 1;
      if (s === 'high') high += 1;
    });
    return { potholes, defects, congestion, critical, high };
  }, [events]);

  const handleStatusUpdate = async (eventId, newStatus) => {
    try {
      const updated = await updateEventStatus(eventId, newStatus);
      setEvents((prev) => prev.map((e) => (e.event_id === eventId ? updated : e)));
      setSelectedEvent(updated);
    } catch (err) {
      console.error('[EventPage] Status update failed:', err);
    }
  };

  const clearFilters = () => {
    setSearchTerm('');
    setFilterType('all');
    setFilterSeverity('all');
    setFilterStatus('all');
  };

  const hasActiveFilters = searchTerm.trim() !== '' || filterType !== 'all' || filterSeverity !== 'all' || filterStatus !== 'all';

  const getSeverityColor = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'critical':
      case 'very high':
      case 'very_high':
        return 'bg-red-100 text-red-700';
      case 'high':
        return 'bg-orange-100 text-orange-700';
      case 'medium':
        return 'bg-amber-100 text-amber-700';
      case 'low':
        return 'bg-green-100 text-green-700';
      default:
        return 'bg-slate-100 text-slate-700';
    }
  };

  const getStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'new':
        return 'bg-blue-100 text-blue-700';
      case 'under_review':
        return 'bg-purple-100 text-purple-700';
      case 'verified':
        return 'bg-emerald-100 text-emerald-700';
      case 'resolved':
        return 'bg-slate-100 text-slate-700';
      default:
        return 'bg-slate-100 text-slate-700';
    }
  };


  if (loading && events.length === 0) {
    return <LoadingState message="Loading detected incidents and events..." />;
  }

  if (error && events.length === 0) {
    return (
      <ErrorState
        title="Events Feed Unavailable"
        message="Could not load telemetry events. You can retry the connection or switch to Demo Mode."
        onRetry={loadData}
      />
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3">
        <div className="flex justify-between items-end">
          <div>
            <div className="flex items-center gap-3">
              <h2 className="text-2xl font-bold text-slate-800">Incident & Event Management</h2>
              {isWsConnected && (
                <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                  <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                  Live Stream Active
                </span>
              )}
            </div>
            <p className="text-slate-500 text-xs mt-0.5">Review and manage urban intelligence events detected by the fleet.</p>
          </div>
          <div className="flex gap-3">
            <div className="relative">
              <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
              <input 
                type="text" 
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search by ID, bus, type..." 
                className="pl-9 pr-8 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 w-64 bg-white"
              />
              {searchTerm && (
                <button 
                  onClick={() => setSearchTerm('')} 
                  className="absolute right-2.5 top-2.5 text-slate-400 hover:text-slate-600 cursor-pointer"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>
            <button 
              onClick={() => setShowFilters(!showFilters)}
              className={`flex items-center gap-2 px-4 py-2 border rounded-md text-sm font-medium transition-colors cursor-pointer ${
                showFilters || hasActiveFilters
                  ? 'bg-brand-50 border-brand-500 text-brand-700'
                  : 'bg-white border-slate-300 text-slate-700 hover:bg-slate-50'
              }`}
            >
              <Filter className="w-4 h-4" />
              <span>Filters</span>
              {hasActiveFilters && (
                <span className="w-2 h-2 rounded-full bg-brand-600"></span>
              )}
            </button>
          </div>
        </div>

        {/* Filter Panel */}
        {showFilters && (
          <div className="bg-white p-4 rounded-lg shadow-sm border border-slate-200 grid grid-cols-1 sm:grid-cols-4 gap-4 animate-in fade-in duration-150">
            <div>
              <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">Event Type</label>
              <select 
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                className="w-full text-sm border border-slate-300 rounded-md p-2 bg-white focus:outline-none focus:border-brand-500"
              >
                <option value="all">All Types</option>
                <option value="pothole">Pothole</option>
                <option value="road_defect">Road Defect</option>
                <option value="congestion">Congestion</option>
                <option value="vehicle_count">Vehicle Count</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">Severity</label>
              <select 
                value={filterSeverity}
                onChange={(e) => setFilterSeverity(e.target.value)}
                className="w-full text-sm border border-slate-300 rounded-md p-2 bg-white focus:outline-none focus:border-brand-500"
              >
                <option value="all">All Severities</option>
                <option value="critical">Critical</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">Status</label>
              <select 
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                className="w-full text-sm border border-slate-300 rounded-md p-2 bg-white focus:outline-none focus:border-brand-500"
              >
                <option value="all">All Statuses</option>
                <option value="new">New</option>
                <option value="under_review">Under Review</option>
                <option value="verified">Verified</option>
                <option value="resolved">Resolved</option>
              </select>
            </div>

            <div className="flex items-end">
              <button 
                onClick={clearFilters}
                disabled={!hasActiveFilters}
                className="w-full py-2 px-3 text-sm font-medium border border-slate-200 text-slate-600 rounded-md hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
              >
                Reset Filters
              </button>
            </div>
          </div>
        )}

        {/* Quick Filter Buttons Bar & Count Header */}
        <div className="flex items-center justify-between gap-3 flex-wrap pt-1">
          <div className="flex items-center gap-2 flex-wrap">
            <button
              onClick={() => { setFilterType('all'); setFilterSeverity('all'); setFilterStatus('all'); }}
              className={`px-3 py-1 rounded-full text-xs font-semibold border transition cursor-pointer ${
                filterType === 'all' && filterSeverity === 'all' && filterStatus === 'all'
                  ? 'bg-slate-900 text-white border-slate-900 shadow-xs'
                  : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
              }`}
            >
              All ({events.length})
            </button>
            <button
              onClick={() => setFilterType(filterType === 'pothole' ? 'all' : 'pothole')}
              className={`px-3 py-1 rounded-full text-xs font-semibold border transition cursor-pointer ${
                filterType === 'pothole'
                  ? 'bg-amber-600 text-white border-amber-600 shadow-xs'
                  : 'bg-white text-slate-600 border-slate-200 hover:bg-amber-50 hover:text-amber-700'
              }`}
            >
              Potholes ({counts.potholes})
            </button>
            <button
              onClick={() => setFilterType(filterType === 'road_defect' ? 'all' : 'road_defect')}
              className={`px-3 py-1 rounded-full text-xs font-semibold border transition cursor-pointer ${
                filterType === 'road_defect'
                  ? 'bg-orange-600 text-white border-orange-600 shadow-xs'
                  : 'bg-white text-slate-600 border-slate-200 hover:bg-orange-50 hover:text-orange-700'
              }`}
            >
              Road Defects ({counts.defects})
            </button>
            <button
              onClick={() => setFilterType(filterType === 'congestion' ? 'all' : 'congestion')}
              className={`px-3 py-1 rounded-full text-xs font-semibold border transition cursor-pointer ${
                filterType === 'congestion'
                  ? 'bg-blue-600 text-white border-blue-600 shadow-xs'
                  : 'bg-white text-slate-600 border-slate-200 hover:bg-blue-50 hover:text-blue-700'
              }`}
            >
              Congestion ({counts.congestion})
            </button>
            <button
              onClick={() => setFilterSeverity(filterSeverity === 'critical' ? 'all' : 'critical')}
              className={`px-3 py-1 rounded-full text-xs font-semibold border transition cursor-pointer ${
                filterSeverity === 'critical'
                  ? 'bg-red-600 text-white border-red-600 shadow-xs'
                  : 'bg-white text-slate-600 border-slate-200 hover:bg-red-50 hover:text-red-700'
              }`}
            >
              Critical ({counts.critical})
            </button>
            <button
              onClick={() => setFilterSeverity(filterSeverity === 'high' ? 'all' : 'high')}
              className={`px-3 py-1 rounded-full text-xs font-semibold border transition cursor-pointer ${
                filterSeverity === 'high'
                  ? 'bg-amber-600 text-white border-amber-600 shadow-xs'
                  : 'bg-white text-slate-600 border-slate-200 hover:bg-amber-50 hover:text-amber-700'
              }`}
            >
              High ({counts.high})
            </button>
          </div>

          <div className="text-xs text-slate-500 font-medium ml-auto flex items-center gap-2">
            <span>
              Showing <strong className="text-slate-800 font-bold">{filteredEvents.length}</strong> of{' '}
              <strong className="text-slate-800">{events.length}</strong> events
            </span>
            {hasActiveFilters && (
              <button
                onClick={clearFilters}
                className="text-brand-600 hover:text-brand-800 font-semibold underline cursor-pointer ml-1"
              >
                Reset filters
              </button>
            )}
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-xs border border-slate-200 overflow-hidden">
        {filteredEvents.length === 0 ? (
          <div className="p-12 text-center text-slate-500 text-sm space-y-3">
            <p className="font-semibold text-slate-700">No events match the selected search or filters.</p>
            {hasActiveFilters && (
              <button
                onClick={clearFilters}
                className="px-4 py-1.5 bg-slate-900 text-white text-xs font-semibold rounded-md hover:bg-slate-800 cursor-pointer transition shadow-xs"
              >
                Clear All Filters
              </button>
            )}
          </div>
        ) : (
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-sm text-slate-600">
                <th className="p-4 font-semibold w-20">Evidence</th>
                <th className="p-4 font-semibold">Event ID</th>
                <th className="p-4 font-semibold">Type</th>
                <th className="p-4 font-semibold">Severity</th>
                <th className="p-4 font-semibold">Bus / Camera</th>
                <th className="p-4 font-semibold">Time</th>
                <th className="p-4 font-semibold">Status</th>
                <th className="p-4 font-semibold">Action</th>
              </tr>
            </thead>
            <tbody>
              {filteredEvents.map((event) => (
                <tr 
                  key={event.event_id} 
                  className={`border-b border-slate-100 hover:bg-slate-50 transition-colors cursor-pointer ${
                    selectedEvent?.event_id === event.event_id ? 'bg-brand-50/40' : ''
                  }`}
                  onClick={() => setSelectedEvent(event)}
                >
                  <td className="p-3 w-20" onClick={(e) => { e.stopPropagation(); setSelectedEvent(event); }}>
                    <div 
                      className="relative w-16 h-10 rounded overflow-hidden border border-slate-200 bg-slate-900 shadow-xs hover:border-brand-500 transition-all cursor-pointer group"
                      title="Click to view full captured evidence & AI detection"
                    >
                      <img
                        src={getEvidenceFrameUrl(event)}
                        alt={event.event_id}
                        className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-200"
                        onError={(e) => {
                          e.target.onerror = null;
                          e.target.src = '/evidence/pothole_city_front.jpg';
                        }}
                      />
                      <div className="absolute inset-0 bg-black/25 opacity-0 group-hover:opacity-100 flex items-center justify-center transition-opacity">
                        <Eye className="w-3.5 h-3.5 text-white drop-shadow" />
                      </div>
                    </div>
                  </td>
                  <td className="p-4 font-medium text-slate-800">{event.event_id}</td>
                  <td className="p-4 capitalize">{(event.event_type || '').replace('_', ' ')}</td>
                  <td className="p-4">
                    <span className={`px-2 py-1 rounded text-xs font-bold uppercase tracking-wider ${getSeverityColor(event.severity)}`}>
                      {event.severity}
                    </span>
                  </td>
                  <td className="p-4">
                    <div className="text-sm font-medium">{event.bus_id}</div>
                    <div className="text-xs text-slate-500">{event.camera_id || 'CAM_FRONT'}</div>
                  </td>
                  <td className="p-4 text-sm">
                    <div className="font-semibold text-slate-800">
                      {formatDateTime(event.timestamp, 'dd MMM yyyy, HH:mm:ss')}
                    </div>
                    <div className="text-xs text-brand-600 font-medium mt-0.5">
                      {formatRelativeTime(event.timestamp)}
                    </div>
                  </td>
                  <td className="p-4">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium capitalize ${getStatusColor(event.status)}`}>
                      {(event.status || 'new').replace('_', ' ')}
                    </span>
                  </td>
                  <td className="p-4">
                    <button 
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedEvent(event);
                      }}
                      className="text-brand-600 hover:text-brand-800 flex items-center gap-1 text-sm font-medium cursor-pointer"
                    >
                      <Eye className="w-4 h-4" /> View
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Event Details Modal */}
      {selectedEvent && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center z-50 p-4">
          <div
            className={`bg-white rounded-xl shadow-2xl w-full ${
              isEvidenceExpanded ? 'max-w-4xl max-h-[94vh]' : 'max-w-2xl max-h-full'
            } overflow-hidden flex flex-col transition-all duration-300 relative`}
          >
            <div className="p-4 border-b border-slate-200 flex justify-between items-center bg-slate-50">
              <h3 className="font-bold text-lg flex items-center gap-2 text-slate-800">
                <AlertTriangle className="w-5 h-5 text-amber-500" />
                {(selectedEvent.event_type || 'INCIDENT').replace('_', ' ').toUpperCase()} DETECTED
              </h3>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setIsEvidenceExpanded(!isEvidenceExpanded)}
                  className={`flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-semibold border transition cursor-pointer ${
                    isEvidenceExpanded
                      ? 'bg-brand-50 border-brand-300 text-brand-700 hover:bg-brand-100'
                      : 'bg-white border-slate-300 text-slate-700 hover:bg-slate-100'
                  }`}
                  title={isEvidenceExpanded ? 'Collapse to standard view' : 'Expand evidence to cover whole popup'}
                >
                  {isEvidenceExpanded ? (
                    <>
                      <Minimize2 className="w-3.5 h-3.5" />
                      <span>Standard View</span>
                    </>
                  ) : (
                    <>
                      <Maximize2 className="w-3.5 h-3.5" />
                      <span>Expand Image</span>
                    </>
                  )}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setSelectedEvent(null);
                    setIsEvidenceExpanded(false);
                  }}
                  className="text-slate-500 hover:text-slate-800 text-2xl leading-none cursor-pointer p-1"
                >
                  &times;
                </button>
              </div>
            </div>

            {isEvidenceExpanded ? (
              /* Expanded Mode: The image and live detection cover the whole popup */
              <div className="p-4 flex flex-col flex-1 overflow-y-auto bg-slate-900/5">
                <div className="w-full flex-1 min-h-[400px] flex flex-col justify-center">
                  <CapturedEvidenceViewer
                    event={selectedEvent}
                    isExpanded={true}
                    onToggleExpand={() => setIsEvidenceExpanded(false)}
                    fillModal={true}
                  />
                </div>

                {/* Telemetry and Action Strip while expanded */}
                <div className="mt-3 bg-white p-3 rounded-lg border border-slate-200 flex flex-wrap items-center justify-between gap-3 shadow-xs">
                  <div className="flex flex-wrap items-center gap-4 text-xs">
                    <div>
                      <span className="text-slate-500">Confidence: </span>
                      <span className="font-bold text-slate-800">
                        {Math.round((selectedEvent.confidence || 0.85) * 100)}%
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-500">Severity: </span>
                      <span
                        className={`px-2 py-0.5 rounded text-[11px] font-bold uppercase ${getSeverityColor(
                          selectedEvent.severity
                        )}`}
                      >
                        {selectedEvent.severity}
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-500">Bus: </span>
                      <span className="font-semibold text-slate-800">{selectedEvent.bus_id}</span>
                    </div>
                    <div>
                      <span className="text-slate-500">Location: </span>
                      <span className="font-mono text-slate-800">
                        {selectedEvent.latitude?.toFixed?.(4) ?? selectedEvent.latitude},{' '}
                        {selectedEvent.longitude?.toFixed?.(4) ?? selectedEvent.longitude}
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-500">Captured: </span>
                      <span className="font-semibold text-slate-800">
                        {formatDateTime(selectedEvent.timestamp, 'dd MMM yyyy, HH:mm:ss')}
                      </span>{' '}
                      <span className="text-[11px] text-brand-600 font-medium">
                        ({formatRelativeTime(selectedEvent.timestamp)})
                      </span>
                    </div>
                    {selectedEvent.width_ratio != null && (
                      <div>
                        <span className="text-slate-500">Defect Width: </span>
                        <span className="font-bold text-amber-700">
                          {Math.round(selectedEvent.width_ratio * 100)}%
                        </span>
                      </div>
                    )}
                  </div>

                  <div className="flex items-center gap-1.5 text-xs">
                    <span className="text-slate-500 font-medium">Status:</span>
                    {['new', 'under_review', 'verified', 'resolved'].map((status) => (
                      <button
                        key={status}
                        onClick={() => handleStatusUpdate(selectedEvent.event_id, status)}
                        className={`px-2 py-1 rounded text-xs font-medium capitalize border cursor-pointer ${
                          selectedEvent.status === status
                            ? 'border-brand-500 bg-brand-50 text-brand-700'
                            : 'border-slate-300 bg-white text-slate-600 hover:bg-slate-50'
                        }`}
                      >
                        {status.replace('_', ' ')}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              /* Standard 2-column view */
              <div className="p-6 overflow-y-auto">
                <div className="flex gap-6 mb-6">
                  <div className="w-1/2">
                    <CapturedEvidenceViewer
                      event={selectedEvent}
                      isExpanded={false}
                      onToggleExpand={() => setIsEvidenceExpanded(true)}
                    />
                    <p className="text-xs text-center text-slate-500 mt-1 font-medium">Captured Evidence</p>
                  </div>
                
                <div className="w-1/2 space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-xs text-slate-500 uppercase font-semibold">Confidence</p>
                      <p className="font-medium text-lg">{Math.round((selectedEvent.confidence || 0.85) * 100)}%</p>
                    </div>
                    <div>
                      <p className="text-xs text-slate-500 uppercase font-semibold">Severity</p>
                      <span className={`px-2 py-0.5 rounded text-xs font-bold uppercase ${getSeverityColor(selectedEvent.severity)}`}>
                        {selectedEvent.severity}
                      </span>
                    </div>
                    <div>
                      <p className="text-xs text-slate-500 uppercase font-semibold">Bus</p>
                      <p className="font-medium">{selectedEvent.bus_id}</p>
                    </div>
                    <div>
                      <p className="text-xs text-slate-500 uppercase font-semibold">Camera</p>
                      <p className="font-medium">{selectedEvent.camera_id || 'CAM_FRONT'}</p>
                    </div>
                  </div>
                  
                  <div className="border-t border-slate-100 pt-4">
                    <p className="text-xs text-slate-500 uppercase font-semibold">Location</p>
                    <p className="font-mono text-sm">{selectedEvent.latitude?.toFixed?.(4) ?? selectedEvent.latitude}, {selectedEvent.longitude?.toFixed?.(4) ?? selectedEvent.longitude}</p>
                  </div>

                  <div className="border-t border-slate-100 pt-3">
                    <p className="text-xs text-slate-500 uppercase font-semibold">Captured Timestamp</p>
                    <p className="font-semibold text-slate-800 text-sm">{formatDateTime(selectedEvent.timestamp, 'dd MMM yyyy, HH:mm:ss')}</p>
                    <p className="text-xs text-brand-600 font-medium mt-0.5">{formatRelativeTime(selectedEvent.timestamp)}</p>
                  </div>
                  
                  <div>
                    <p className="text-xs text-slate-500 uppercase font-semibold">Repeated Detection</p>
                    <p className="font-medium text-amber-700 bg-amber-50 inline-block px-2 py-1 rounded text-sm">
                      {selectedEvent.repeated_detections > 1 ? `Yes — ${selectedEvent.repeated_detections} observations` : 'First observation'}
                    </p>
                  </div>

                  {(selectedEvent.width_ratio != null || selectedEvent.severity_method) && (
                    <div className="border-t border-slate-100 pt-3 space-y-1.5 bg-amber-50/50 p-2.5 rounded-md border border-amber-200/60">
                      <p className="text-[11px] uppercase font-bold text-amber-900 tracking-wider">
                        Road Defect Telemetry
                      </p>
                      <div className="grid grid-cols-2 gap-2 text-xs">
                        {selectedEvent.width_ratio != null && (
                          <div>
                            <span className="text-slate-500">Defect Width:</span>{' '}
                            <span className="font-bold text-slate-800">{Math.round(selectedEvent.width_ratio * 100)}%</span>
                          </div>
                        )}
                        {selectedEvent.area_ratio != null && (
                          <div>
                            <span className="text-slate-500">Area Ratio:</span>{' '}
                            <span className="font-bold text-slate-800">{(selectedEvent.area_ratio * 100).toFixed(2)}%</span>
                          </div>
                        )}
                      </div>
                      {selectedEvent.severity_method && (
                        <p className="text-[11px] text-amber-800 font-mono">
                          Method: {selectedEvent.severity_method}
                        </p>
                      )}
                    </div>
                  )}
                </div>
              </div>
              
              <div className="bg-slate-50 p-4 rounded-lg border border-slate-200">
                <p className="text-sm font-semibold mb-2 text-slate-700">Update Status</p>
                <div className="flex gap-2">
                  {['new', 'under_review', 'verified', 'resolved'].map(status => (
                    <button 
                      key={status}
                      onClick={() => handleStatusUpdate(selectedEvent.event_id, status)}
                      className={`px-3 py-1.5 rounded text-sm font-medium capitalize border cursor-pointer ${
                        selectedEvent.status === status 
                          ? 'border-brand-500 bg-brand-50 text-brand-700'
                          : 'border-slate-300 bg-white text-slate-600 hover:bg-slate-50'
                      }`}
                    >
                      {status.replace('_', ' ')}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    )}
  </div>
);
}
