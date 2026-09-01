import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { getEvents } from '../services/api';
import { Layers, Filter } from 'lucide-react';

// Fix for default marker icons in react-leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Custom Icons for different events
const createCustomIcon = (color) => {
  return new L.Icon({
    iconUrl: `https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-${color}.png`,
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
  });
};

const potholeIcon = createCustomIcon('red');
const congestionIcon = createCustomIcon('orange');
const defaultIcon = createCustomIcon('blue');

export default function GISMapPage() {
  const [events, setEvents] = useState([]);
  
  // Delhi coordinates as center
  const center = [28.6139, 77.2090];

  useEffect(() => {
    async function loadData() {
      const data = await getEvents();
      setEvents(data);
    }
    loadData();
  }, []);

  const getMarkerIcon = (type) => {
    if (type === 'pothole') return potholeIcon;
    if (type === 'congestion') return congestionIcon;
    return defaultIcon;
  };

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      <div className="flex justify-between items-center mb-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-800">GIS Urban Intelligence Map</h2>
        </div>
        <div className="flex gap-2 text-sm">
          <button className="px-4 py-2 bg-white border border-slate-300 rounded-md font-medium text-slate-700 hover:bg-slate-50 flex items-center gap-2">
            <Filter className="w-4 h-4" /> Filter Events
          </button>
          <button className="px-4 py-2 bg-white border border-slate-300 rounded-md font-medium text-slate-700 hover:bg-slate-50 flex items-center gap-2">
            <Layers className="w-4 h-4" /> Heatmap Layer
          </button>
        </div>
      </div>

      <div className="flex-1 bg-white rounded-lg shadow border border-slate-200 overflow-hidden relative">
        <MapContainer center={center} zoom={12} className="w-full h-full">
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          
          {events.map((event) => (
            <React.Fragment key={event.event_id}>
              {/* Highlight repeated detections with a circle */}
              {event.repeated_detections > 2 && (
                <Circle 
                  center={[event.latitude, event.longitude]} 
                  radius={400} 
                  pathOptions={{ color: 'red', fillColor: 'red', fillOpacity: 0.2 }}
                />
              )}
              
              <Marker 
                position={[event.latitude, event.longitude]}
                icon={getMarkerIcon(event.event_type)}
              >
                <Popup>
                  <div className="p-1 min-w-[200px]">
                    <h4 className="font-bold uppercase border-b pb-1 mb-2 flex justify-between">
                      {event.event_type.replace('_', ' ')}
                      <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                        event.severity === 'high' ? 'bg-red-100 text-red-700' : 
                        event.severity === 'medium' ? 'bg-amber-100 text-amber-700' : 'bg-green-100 text-green-700'
                      }`}>{event.severity}</span>
                    </h4>
                    
                    <div className="text-sm space-y-1 mb-3">
                      <p><span className="text-gray-500">Event ID:</span> {event.event_id}</p>
                      <p><span className="text-gray-500">Confidence:</span> {Math.round(event.confidence * 100)}%</p>
                      {event.repeated_detections > 1 && (
                        <p className="text-red-600 font-semibold mt-1">
                          Persistent Issue: {event.repeated_detections} detections
                        </p>
                      )}
                    </div>
                    
                    <button className="w-full bg-slate-900 text-white text-xs py-1.5 rounded hover:bg-slate-800 transition">
                      View Details
                    </button>
                  </div>
                </Popup>
              </Marker>
            </React.Fragment>
          ))}
        </MapContainer>

        {/* Floating Legend */}
        <div className="absolute bottom-6 right-6 z-[400] bg-white p-4 rounded shadow-lg border border-slate-200">
          <h4 className="font-bold text-sm mb-3 text-slate-800 border-b pb-1">Map Legend</h4>
          <div className="space-y-2 text-sm text-slate-600">
            <div className="flex items-center gap-2">
              <img src="https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png" className="h-6" alt="Red Marker" />
              <span>Pothole / Defect</span>
            </div>
            <div className="flex items-center gap-2">
              <img src="https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-orange.png" className="h-6" alt="Orange Marker" />
              <span>Traffic Congestion</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-red-500/20 border-2 border-red-500 rounded-full ml-1 mr-1"></div>
              <span>Persistent Hotspot</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
