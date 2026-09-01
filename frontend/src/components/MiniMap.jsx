import React from 'react';
import { MapContainer, TileLayer, Marker, Circle } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Mini map uses simpler styling and disables zoom/scroll to act as a dashboard widget
export default function MiniMap({ events }) {
  const center = [28.6139, 77.2090]; // Delhi Center

  // Basic red dot icon for the mini-map to keep it clean
  const dotIcon = new L.Icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
    iconSize: [16, 26],
    iconAnchor: [8, 26],
    shadowSize: [26, 26]
  });

  return (
    <div className="w-full h-full relative z-0">
      <MapContainer 
        center={center} 
        zoom={11} 
        className="w-full h-full"
        zoomControl={false}
        scrollWheelZoom={false}
        dragging={false}
        doubleClickZoom={false}
      >
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>'
        />
        
        {events && events.map((event) => (
          <React.Fragment key={`mini-${event.event_id}`}>
            {event.repeated_detections > 2 && (
              <Circle 
                center={[event.latitude, event.longitude]} 
                radius={600} 
                pathOptions={{ color: '#ef4444', fillColor: '#ef4444', fillOpacity: 0.3, stroke: false }}
              />
            )}
            <Marker 
              position={[event.latitude, event.longitude]}
              icon={dotIcon}
            />
          </React.Fragment>
        ))}
      </MapContainer>
      
      {/* Overlay to encourage clicking to the full GIS Map */}
      <div className="absolute inset-0 bg-gradient-to-t from-slate-900/40 to-transparent z-[400] flex items-end justify-center pb-4 pointer-events-none">
        <span className="bg-white/90 backdrop-blur text-slate-800 text-sm font-semibold px-4 py-2 rounded-full shadow-lg">
          Interactive GIS active in Map tab
        </span>
      </div>
    </div>
  );
}
