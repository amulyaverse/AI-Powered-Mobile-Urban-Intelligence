import React, { useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { getEvents, updateEventStatus } from '../services/api';
import { format } from 'date-fns';
import { Filter, Search, Eye, AlertTriangle, X, SlidersHorizontal } from 'lucide-react';

export default function EventPage() {
  const location = useLocation();
  const [events, setEvents] = useState([]);
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [filterType, setFilterType] = useState('all');
  const [filterSeverity, setFilterSeverity] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all');
  const [loading, setLoading] = useState(false);

  const loadData = async () => {
    setLoading(true);
    try {
      const query = {};
      if (searchTerm.trim()) query.search = searchTerm.trim();
      if (filterType !== 'all') query.event_type = filterType;
      if (filterSeverity !== 'all') query.severity = filterSeverity;
      if (filterStatus !== 'all') query.status = filterStatus;

      const data = await getEvents(query);
      setEvents(data);

      // Auto-open if selectedEventId was passed via route state
      if (location.state?.selectedEventId) {
        const target = data.find((e) => e.event_id === location.state.selectedEventId);
        if (target) setSelectedEvent(target);
      }
    } catch (err) {
      console.error('Failed to load events:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const timer = setTimeout(() => {
      loadData();
    }, 250);
    return () => clearTimeout(timer);
  }, [searchTerm, filterType, filterSeverity, filterStatus]);

  const handleStatusUpdate = async (eventId, newStatus) => {
    try {
      const updated = await updateEventStatus(eventId, newStatus);
      setEvents((prev) => prev.map((e) => (e.event_id === eventId ? updated : e)));
      setSelectedEvent(updated);
    } catch (err) {
      console.error('Status update failed:', err);
    }
  };

  const clearFilters = () => {
    setSearchTerm('');
    setFilterType('all');
    setFilterSeverity('all');
    setFilterStatus('all');
  };

  const hasActiveFilters = searchTerm || filterType !== 'all' || filterSeverity !== 'all' || filterStatus !== 'all';


  const getSeverityColor = (severity) => {
    switch(severity) {
      case 'high': return 'bg-red-100 text-red-700';
      case 'medium': return 'bg-amber-100 text-amber-700';
      case 'low': return 'bg-green-100 text-green-700';
      default: return 'bg-slate-100 text-slate-700';
    }
  };

  const getStatusColor = (status) => {
    switch(status) {
      case 'new': return 'bg-blue-100 text-blue-700';
      case 'under_review': return 'bg-purple-100 text-purple-700';
      case 'verified': return 'bg-emerald-100 text-emerald-700';
      case 'resolved': return 'bg-slate-100 text-slate-700';
      default: return 'bg-slate-100 text-slate-700';
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3">
        <div className="flex justify-between items-end">
          <div>
            <h2 className="text-2xl font-bold text-slate-800">Incident & Event Management</h2>
            <p className="text-slate-500">Review and manage urban intelligence events detected by the fleet.</p>
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
                  className="absolute right-2.5 top-2.5 text-slate-400 hover:text-slate-600"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>
            <button 
              onClick={() => setShowFilters(!showFilters)}
              className={`flex items-center gap-2 px-4 py-2 border rounded-md text-sm font-medium transition-colors ${
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
                className="w-full py-2 px-3 text-sm font-medium border border-slate-200 text-slate-600 rounded-md hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed"
              >
                Reset Filters
              </button>
            </div>
          </div>
        )}
      </div>

      <div className="bg-white rounded-lg shadow border border-slate-200 overflow-hidden">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-slate-50 border-b border-slate-200 text-sm text-slate-600">
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
            {events.map((event) => (
              <tr key={event.event_id} className="border-b border-slate-100 hover:bg-slate-50">
                <td className="p-4 font-medium text-slate-800">{event.event_id}</td>
                <td className="p-4 capitalize">{event.event_type.replace('_', ' ')}</td>
                <td className="p-4">
                  <span className={`px-2 py-1 rounded text-xs font-bold uppercase tracking-wider ${getSeverityColor(event.severity)}`}>
                    {event.severity}
                  </span>
                </td>
                <td className="p-4">
                  <div className="text-sm font-medium">{event.bus_id}</div>
                  <div className="text-xs text-slate-500">{event.camera_id}</div>
                </td>
                <td className="p-4 text-sm text-slate-600">
                  {format(new Date(event.timestamp), 'dd MMM yyyy, HH:mm')}
                </td>
                <td className="p-4">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium capitalize ${getStatusColor(event.status)}`}>
                    {event.status.replace('_', ' ')}
                  </span>
                </td>
                <td className="p-4">
                  <button 
                    onClick={() => setSelectedEvent(event)}
                    className="text-brand-600 hover:text-brand-800 flex items-center gap-1 text-sm font-medium"
                  >
                    <Eye className="w-4 h-4" /> View
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Event Details Modal */}
      {selectedEvent && (
        <div className="fixed inset-0 bg-slate-900/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl overflow-hidden flex flex-col max-h-full">
            <div className="p-4 border-b border-slate-200 flex justify-between items-center bg-slate-50">
              <h3 className="font-bold text-lg flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-amber-500" />
                {selectedEvent.event_type.replace('_', ' ').toUpperCase()} DETECTED
              </h3>
              <button onClick={() => setSelectedEvent(null)} className="text-slate-500 hover:text-slate-800 text-2xl leading-none">&times;</button>
            </div>
            
            <div className="p-6 overflow-y-auto">
              <div className="flex gap-6 mb-6">
                <div className="w-1/2">
                  <div className="aspect-video bg-slate-100 rounded-lg overflow-hidden border border-slate-200">
                    <img src={selectedEvent.evidence} alt="Event Evidence" className="w-full h-full object-cover" />
                  </div>
                  <p className="text-xs text-center text-slate-500 mt-2">Captured Evidence</p>
                </div>
                
                <div className="w-1/2 space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-xs text-slate-500 uppercase font-semibold">Confidence</p>
                      <p className="font-medium text-lg">{Math.round(selectedEvent.confidence * 100)}%</p>
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
                      <p className="font-medium">{selectedEvent.camera_id}</p>
                    </div>
                  </div>
                  
                  <div className="border-t border-slate-100 pt-4">
                    <p className="text-xs text-slate-500 uppercase font-semibold">Location</p>
                    <p className="font-mono text-sm">{selectedEvent.latitude}, {selectedEvent.longitude}</p>
                  </div>
                  
                  <div>
                    <p className="text-xs text-slate-500 uppercase font-semibold">Repeated Detection</p>
                    <p className="font-medium text-amber-700 bg-amber-50 inline-block px-2 py-1 rounded text-sm">
                      Yes — {selectedEvent.repeated_detections} observations
                    </p>
                  </div>
                </div>
              </div>
              
              <div className="bg-slate-50 p-4 rounded-lg border border-slate-200">
                <p className="text-sm font-semibold mb-2">Update Status</p>
                <div className="flex gap-2">
                  {['new', 'under_review', 'verified', 'resolved'].map(status => (
                    <button 
                      key={status}
                      onClick={() => handleStatusUpdate(selectedEvent.event_id, status)}
                      className={`px-3 py-1.5 rounded text-sm font-medium capitalize border ${
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
          </div>
        </div>
      )}
    </div>
  );
}
