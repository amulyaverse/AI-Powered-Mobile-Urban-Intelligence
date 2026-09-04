import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { MapContainer, TileLayer, Marker, Popup, Circle } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { getEvents, getHotspots } from '../services/api';
import { Layers, Filter, Flame, Check } from 'lucide-react';

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
    shadowSize: [41, 41],
  });
};

const potholeIcon = createCustomIcon('red');
const congestionIcon = createCustomIcon('orange');
const defaultIcon = createCustomIcon('blue');

export default function GISMapPage() {
  const navigate = useNavigate();
  const [events, setEvents] = useState([]);
  const [hotspots, setHotspots] = useState([]);
  const [selectedType, setSelectedType] = useState('all');
  const [showFilterDropdown, setShowFilterDropdown] = useState(false);
  const [showHeatmap, setShowHeatmap] = useState(true);

  // Delhi coordinates as center
  const center = [28.6139, 77.2090];

  useEffect(() => {
    async function loadData() {
      try {
        const query = selectedType !== 'all' ? { event_type: selectedType } : {};
        const [eventsData, hotspotsData] = await Promise.all([
          getEvents(query),
          getHotspots('active'),
        ]);
        setEvents(eventsData);
        setHotspots(hotspotsData);
      } catch (err) {
        console.error('Failed to load GIS data:', err);
      }
    }
    loadData();
  }, [selectedType]);

  const getMarkerIcon = (type) => {
    if (type === 'pothole') return potholeIcon;
    if (type === 'congestion') return congestionIcon;
    return defaultIcon;
  };

  const getHotspotColor = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'critical':
      case 'high':
        return '#ef4444'; // red
      case 'medium':
        return '#f97316'; // orange
      default:
        return '#3b82f6'; // blue
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      <div className="flex justify-between items-center mb-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-800">GIS Urban Intelligence Map</h2>
          <p className="text-xs text-slate-500">
            Showing {events.length} events {showHeatmap && `· ${hotspots.length} persistent hotspot clusters`}
          </p>
        </div>
        <div className="flex gap-2 text-sm relative">
          {/* Filter Events Dropdown */}
          <div className="relative">
            <button
              onClick={() => setShowFilterDropdown(!showFilterDropdown)}
              className={`px-4 py-2 border rounded-md font-medium flex items-center gap-2 transition-colors ${
                selectedType !== 'all'
                  ? 'bg-brand-50 border-brand-500 text-brand-700'
                  : 'bg-white border-slate-300 text-slate-700 hover:bg-slate-50'
              }`}
            >
              <Filter className="w-4 h-4" />
              <span>{selectedType === 'all' ? 'Filter Events' : `Type: ${selectedType.replace('_', ' ')}`}</span>
            </button>

            {showFilterDropdown && (
              <div className="absolute right-0 mt-1 w-48 bg-white border border-slate-200 rounded-md shadow-lg z-[500] py-1 text-sm">
                {[
                  { value: 'all', label: 'All Events' },
                  { value: 'pothole', label: 'Potholes' },
                  { value: 'road_defect', label: 'Road Defects' },
                  { value: 'congestion', label: 'Congestion' },
                ].map((opt) => (
                  <button
                    key={opt.value}
                    onClick={() => {
                      setSelectedType(opt.value);
                      setShowFilterDropdown(false);
                    }}
                    className="w-full text-left px-4 py-2 hover:bg-slate-50 flex items-center justify-between text-slate-700"
                  >
                    <span>{opt.label}</span>
                    {selectedType === opt.value && <Check className="w-4 h-4 text-brand-600" />}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Heatmap Layer Toggle */}
          <button
            onClick={() => setShowHeatmap(!showHeatmap)}
            className={`px-4 py-2 border rounded-md font-medium flex items-center gap-2 transition-colors ${
              showHeatmap
                ? 'bg-amber-50 border-amber-500 text-amber-800'
                : 'bg-white border-slate-300 text-slate-700 hover:bg-slate-50'
            }`}
          >
            <Flame className={`w-4 h-4 ${showHeatmap ? 'text-amber-600' : 'text-slate-500'}`} />
            <span>Heatmap Layer {showHeatmap ? '(ON)' : '(OFF)'}</span>
          </button>
        </div>
      </div>

      <div className="flex-1 bg-white rounded-lg shadow border border-slate-200 overflow-hidden relative">
        <MapContainer center={center} zoom={12} className="w-full h-full">
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          {/* Hotspots Heatmap Layer */}
          {showHeatmap &&
            hotspots.map((hs) => {
              const color = getHotspotColor(hs.severity);
              const radius = Math.max(300, Math.min(750, hs.detection_count * 100));
              return (
                <Circle
                  key={`hotspot-${hs.id}`}
                  center={[hs.center_lat, hs.center_lng]}
                  radius={radius}
                  pathOptions={{
                    color: color,
                    fillColor: color,
                    fillOpacity: 0.25,
                    weight: 2,
                  }}
                >
                  <Popup>
                    <div className="p-1 min-w-[200px]">
                      <h4 className="font-bold border-b pb-1 mb-2 flex justify-between items-center text-slate-800">
                        <span>HOTSPOT #{hs.id}</span>
                        <span
                          className={`text-[10px] px-1.5 py-0.5 rounded font-bold uppercase ${
                            hs.severity === 'high' || hs.severity === 'critical'
                              ? 'bg-red-100 text-red-700'
                              : 'bg-amber-100 text-amber-700'
                          }`}
                        >
                          {hs.severity}
                        </span>
                      </h4>
                      <div className="text-xs space-y-1 mb-2">
                        <p>
                          <span className="text-slate-500">Cluster Type:</span>{' '}
                          <b className="capitalize">{hs.event_type.replace('_', ' ')}</b>
                        </p>
                        <p>
                          <span className="text-slate-500">Observations:</span>{' '}
                          <b className="text-red-600">{hs.detection_count} buses</b>
                        </p>
                        <p>
                          <span className="text-slate-500">Priority Score:</span>{' '}
                          <b>{hs.priority_score.toFixed(1)}</b>
                        </p>
                      </div>
                    </div>
                  </Popup>
                </Circle>
              );
            })}

          {/* Event Markers */}
          {events.map((event) => (
            <Marker
              key={event.event_id}
              position={[event.latitude, event.longitude]}
              icon={getMarkerIcon(event.event_type)}
            >
              <Popup>
                <div className="p-1 min-w-[210px]">
                  <h4 className="font-bold uppercase border-b pb-1 mb-2 flex justify-between items-center">
                    <span>{event.event_type.replace('_', ' ')}</span>
                    <span
                      className={`text-[10px] px-1.5 py-0.5 rounded ${
                        event.severity === 'high'
                          ? 'bg-red-100 text-red-700'
                          : event.severity === 'medium'
                          ? 'bg-amber-100 text-amber-700'
                          : 'bg-green-100 text-green-700'
                      }`}
                    >
                      {event.severity}
                    </span>
                  </h4>

                  <div className="text-sm space-y-1 mb-3">
                    <p>
                      <span className="text-gray-500">Event ID:</span> {event.event_id}
                    </p>
                    <p>
                      <span className="text-gray-500">Confidence:</span> {Math.round(event.confidence * 100)}%
                    </p>
                    {event.repeated_detections > 1 && (
                      <p className="text-red-600 font-semibold text-xs">
                        Persistent Issue: {event.repeated_detections} detections
                      </p>
                    )}
                  </div>

                  <button
                    onClick={() =>
                      navigate('/events', { state: { selectedEventId: event.event_id } })
                    }
                    className="w-full bg-slate-900 text-white text-xs py-1.5 rounded hover:bg-slate-800 transition font-medium cursor-pointer"
                  >
                    View Details
                  </button>
                </div>
              </Popup>
            </Marker>
          ))}
        </MapContainer>

        {/* Floating Legend */}
        <div className="absolute bottom-6 right-6 z-[400] bg-white p-4 rounded-lg shadow-lg border border-slate-200 text-xs">
          <h4 className="font-bold text-sm mb-2 text-slate-800 border-b pb-1">Map Legend</h4>
          <div className="space-y-2 text-slate-600">
            <div className="flex items-center gap-2">
              <img
                src="https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png"
                className="h-5"
                alt="Red Marker"
              />
              <span>Pothole / Road Defect</span>
            </div>
            <div className="flex items-center gap-2">
              <img
                src="https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-orange.png"
                className="h-5"
                alt="Orange Marker"
              />
              <span>Traffic Congestion</span>
            </div>
            {showHeatmap && (
              <div className="flex items-center gap-2">
                <div className="w-3.5 h-3.5 bg-red-500/30 border-2 border-red-500 rounded-full"></div>
                <span>Active Hotspot Cluster</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

