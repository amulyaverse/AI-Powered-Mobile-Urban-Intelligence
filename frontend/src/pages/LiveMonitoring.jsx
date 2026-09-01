import React, { useEffect, useState } from 'react';
import { getBuses } from '../services/api';
import { Truck, Video, SignalHigh, AlertCircle } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

export default function LiveMonitoring() {
  const [buses, setBuses] = useState([]);
  const [selectedBus, setSelectedBus] = useState(null);

  useEffect(() => {
    async function loadData() {
      const data = await getBuses();
      setBuses(data);
      if (data.length > 0) setSelectedBus(data[0]);
    }
    loadData();
  }, []);

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      <h2 className="text-2xl font-bold text-slate-800 mb-4">Live Fleet Monitoring</h2>
      
      <div className="flex flex-1 gap-6 overflow-hidden">
        {/* Fleet List */}
        <div className="w-1/3 bg-white rounded-lg shadow border border-slate-200 flex flex-col overflow-hidden">
          <div className="p-4 border-b border-slate-200 bg-slate-50 font-semibold text-slate-700">
            Active Fleet ({buses.length})
          </div>
          <div className="flex-1 overflow-y-auto p-2 space-y-2">
            {buses.map(bus => (
              <button
                key={bus.id}
                onClick={() => setSelectedBus(bus)}
                className={`w-full text-left p-3 rounded border transition-colors ${
                  selectedBus?.id === bus.id 
                    ? 'bg-brand-50 border-brand-200 shadow-sm' 
                    : 'bg-white border-slate-100 hover:bg-slate-50'
                }`}
              >
                <div className="flex justify-between items-center mb-1">
                  <span className="font-bold text-slate-800">{bus.id}</span>
                  <span className={`text-xs px-2 py-1 rounded-full font-medium ${
                    bus.status === 'Active' ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700'
                  }`}>
                    {bus.status}
                  </span>
                </div>
                <div className="text-sm text-slate-500 mb-2">{bus.route}</div>
                <div className="flex gap-4 text-xs text-slate-400 font-medium">
                  <span className="flex items-center gap-1"><Video className="w-3 h-3" /> {bus.cameraStatus}</span>
                  <span className="flex items-center gap-1"><SignalHigh className="w-3 h-3" /> {formatDistanceToNow(new Date(bus.lastUpdate))} ago</span>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Selected Bus Panel */}
        {selectedBus && (
          <div className="flex-1 bg-white rounded-lg shadow border border-slate-200 flex flex-col overflow-hidden">
            <div className="p-4 border-b border-slate-200 bg-slate-50 flex justify-between items-center">
              <div>
                <h3 className="font-bold text-lg text-slate-800">{selectedBus.id}</h3>
                <p className="text-sm text-slate-500">{selectedBus.route}</p>
              </div>
              <div className="flex items-center gap-2">
                <span className="px-3 py-1 bg-blue-100 text-blue-700 text-sm font-medium rounded-full">Traffic: {selectedBus.traffic}</span>
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
                  {selectedBus.lat.toFixed(4)}, {selectedBus.lng.toFixed(4)}
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
                  <p className="font-mono text-slate-700">{selectedBus.lat.toFixed(4)}, {selectedBus.lng.toFixed(4)}</p>
                </div>
                <div className="p-4 border border-slate-200 rounded-lg bg-slate-50">
                  <p className="text-sm text-slate-500 mb-1">Latest Detection</p>
                  <p className="font-semibold text-slate-700 flex items-center gap-2">
                    <AlertCircle className="w-4 h-4 text-amber-500" />
                    Pothole (2 mins ago)
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
