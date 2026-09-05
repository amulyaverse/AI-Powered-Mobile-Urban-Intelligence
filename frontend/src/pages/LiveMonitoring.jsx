import React, { useEffect, useState, useCallback } from 'react';
import { getBuses, getEvents } from '../services/api';
import { Video, SignalHigh, AlertCircle, CheckCircle2 } from 'lucide-react';
import { formatDistanceToNow, isValid } from 'date-fns';
import { LoadingState, ErrorState } from '../components/PageStatusState';

export default function LiveMonitoring() {
  const [buses, setBuses] = useState([]);
  const [selectedBus, setSelectedBus] = useState(null);
  const [latestDetection, setLatestDetection] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadData = useCallback(async (isInitial = false) => {
    if (isInitial) setLoading(true);
    try {
      const data = await getBuses();
      const safeBuses = Array.isArray(data) ? data : [];
      setBuses(safeBuses);
      if (safeBuses.length > 0) {
        setSelectedBus((prev) => (prev ? safeBuses.find((b) => b.id === prev.id) || safeBuses[0] : safeBuses[0]));
      }
      setError(null);
    } catch (err) {
      console.error('[LiveMonitoring] Failed to load buses:', err);
      setError(err.message || 'Failed to load fleet monitoring telemetry.');
    } finally {
      if (isInitial) setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData(true);
    // Poll every 5 seconds for live GPS updates
    const interval = setInterval(() => loadData(false), 5_000);
    return () => clearInterval(interval);
  }, [loadData]);

  useEffect(() => {
    async function loadLatestDetection() {
      if (!selectedBus) return;
      try {
        const evts = await getEvents({ bus_id: selectedBus.id, limit: 1 });
        setLatestDetection(evts && evts.length > 0 ? evts[0] : null);
      } catch (err) {
        console.error('[LiveMonitoring] Failed to load latest detection:', err);
      }
    }
    loadLatestDetection();
  }, [selectedBus?.id]);

  const formatTimeAgo = (dateStr) => {
    if (!dateStr) return 'Just now';
    const d = new Date(dateStr);
    return isValid(d) ? formatDistanceToNow(d) : 'Just now';
  };

  if (loading && buses.length === 0) {
    return <LoadingState message="Connecting to live bus fleet telemetry..." />;
  }

  if (error && buses.length === 0) {
    return (
      <ErrorState
        title="Fleet Telemetry Unavailable"
        message="Could not connect to live bus telemetry feeds. You can retry the connection or switch to Demo Mode."
        onRetry={() => loadData(true)}
      />
    );
  }

  const currentLat = selectedBus ? (selectedBus.last_lat ?? selectedBus.lat ?? 28.5639) : 28.5639;
  const currentLng = selectedBus ? (selectedBus.last_lng ?? selectedBus.lng ?? 77.2090) : 77.2090;
  const currentTraffic = selectedBus ? (selectedBus.last_traffic ?? selectedBus.traffic ?? 'Moderate') : 'Moderate';

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      <h2 className="text-2xl font-bold text-slate-800 mb-4">Live Fleet Monitoring</h2>
      
      <div className="flex flex-1 gap-6 overflow-hidden">
        {/* Fleet List */}
        <div className="w-1/3 bg-white rounded-lg shadow-xs border border-slate-200 flex flex-col overflow-hidden">
          <div className="p-4 border-b border-slate-200 bg-slate-50 font-semibold text-slate-700 flex justify-between items-center">
            <span>Active Fleet</span>
            <span className="text-xs bg-slate-200 px-2 py-0.5 rounded-full font-bold text-slate-700">{buses.length}</span>
          </div>
          <div className="flex-1 overflow-y-auto p-2 space-y-2">
            {buses.length === 0 ? (
              <div className="p-4 text-center text-xs text-slate-400">No active vehicles reporting</div>
            ) : (
              buses.map(bus => (
                <button
                  key={bus.id}
                  onClick={() => setSelectedBus(bus)}
                  className={`w-full text-left p-3 rounded border transition-colors cursor-pointer ${
                    selectedBus?.id === bus.id 
                      ? 'bg-brand-50 border-brand-200 shadow-xs' 
                      : 'bg-white border-slate-100 hover:bg-slate-50'
                  }`}
                >
                  <div className="flex justify-between items-center mb-1">
                    <span className="font-bold text-slate-800">{bus.id}</span>
                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                      bus.status === 'Active' ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700'
                    }`}>
                      {bus.status || 'Active'}
                    </span>
                  </div>
                  <div className="text-sm text-slate-500 mb-2">{bus.route || 'General Patrol'}</div>
                  <div className="flex gap-4 text-xs text-slate-400 font-medium">
                    <span className="flex items-center gap-1">
                      <Video className="w-3 h-3" /> {bus.camera_status || bus.cameraStatus || 'Active'}
                    </span>
                    <span className="flex items-center gap-1">
                      <SignalHigh className="w-3 h-3" /> {formatTimeAgo(bus.last_seen || bus.lastUpdate)} ago
                    </span>
                  </div>
                </button>
              ))
            )}
          </div>
        </div>

        {/* Selected Bus Panel */}
        {selectedBus && (
          <div className="flex-1 bg-white rounded-lg shadow-xs border border-slate-200 flex flex-col overflow-hidden">
            <div className="p-4 border-b border-slate-200 bg-slate-50 flex justify-between items-center">
              <div>
                <h3 className="font-bold text-lg text-slate-800">{selectedBus.id}</h3>
                <p className="text-sm text-slate-500">{selectedBus.route || 'Patrol Unit'}</p>
              </div>
              <div className="flex items-center gap-2">
                <span className="px-3 py-1 bg-blue-100 text-blue-700 text-sm font-medium rounded-full">
                  Traffic: {currentTraffic}
                </span>
              </div>
            </div>
            
            <div className="p-4 flex-1 flex flex-col gap-4 overflow-y-auto">
              {/* Simulated Camera Stream */}
              <div className="bg-slate-900 rounded-lg aspect-video relative flex items-center justify-center overflow-hidden border border-slate-800 shadow-inner">
                <div className="absolute top-4 left-4 flex gap-2">
                  <span className="bg-red-500 text-white text-xs px-2 py-1 rounded uppercase font-bold animate-pulse">Live</span>
                  <span className="bg-black/50 text-white text-xs px-2 py-1 rounded">CAM_FRONT</span>
                </div>
                <div className="absolute top-4 right-4 text-white font-mono text-xs bg-black/50 px-2 py-1 rounded">
                  {typeof currentLat === 'number' ? currentLat.toFixed(4) : currentLat}, {typeof currentLng === 'number' ? currentLng.toFixed(4) : currentLng}
                </div>
                <Video className="w-16 h-16 text-slate-700" />
                <p className="absolute bottom-4 left-4 text-white/50 text-sm">Simulated Camera Stream</p>
                
                {/* Simulated AI Bounding Box overlay */}
                <div className="absolute border-2 border-brand-500 bg-brand-500/20 w-32 h-24 top-1/2 left-1/3 -mt-12 -ml-16 rounded flex items-start p-1">
                  <span className="bg-brand-500 text-white text-[10px] font-bold px-1 rounded">Car 92%</span>
                </div>
              </div>

              {/* Status Grid */}
              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 border border-slate-200 rounded-lg bg-slate-50">
                  <p className="text-sm text-slate-500 mb-1">Current Location</p>
                  <p className="font-mono text-slate-700">
                    {typeof currentLat === 'number' ? currentLat.toFixed(4) : currentLat}, {typeof currentLng === 'number' ? currentLng.toFixed(4) : currentLng}
                  </p>
                </div>
                <div className="p-4 border border-slate-200 rounded-lg bg-slate-50">
                  <p className="text-sm text-slate-500 mb-1">Latest Detection</p>
                  {latestDetection ? (
                    <div className="font-semibold text-slate-700 flex items-center gap-2">
                      <AlertCircle className={`w-4 h-4 ${latestDetection.severity === 'high' ? 'text-red-500' : 'text-amber-500'}`} />
                      <span className="capitalize">{latestDetection.event_type.replace('_', ' ')}</span>
                      <span className="text-xs text-slate-500 font-normal">
                        ({formatTimeAgo(latestDetection.timestamp)} ago)
                      </span>
                    </div>
                  ) : (
                    <p className="text-slate-600 flex items-center gap-2 text-sm">
                      <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                      No recent incidents
                    </p>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
