export const buses = [
  { id: "BUS_021", route: "Route 534", status: "Active", cameraStatus: "Active", lat: 28.5639, lng: 77.2090, traffic: "High", lastUpdate: new Date(Date.now() - 120000).toISOString() },
  { id: "BUS_014", route: "Route 419", status: "Active", cameraStatus: "Active", lat: 28.6239, lng: 77.2290, traffic: "Medium", lastUpdate: new Date(Date.now() - 300000).toISOString() },
  { id: "BUS_032", route: "Route 720", status: "Active", cameraStatus: "Active", lat: 28.6139, lng: 77.2090, traffic: "Low", lastUpdate: new Date(Date.now() - 60000).toISOString() },
  { id: "BUS_045", route: "Route 534", status: "Active", cameraStatus: "Active", lat: 28.5739, lng: 77.2190, traffic: "High", lastUpdate: new Date(Date.now() - 500000).toISOString() },
  { id: "BUS_017", route: "Route 312", status: "Maintenance", cameraStatus: "Offline", lat: 28.6539, lng: 77.2390, traffic: "Unknown", lastUpdate: new Date(Date.now() - 86400000).toISOString() },
  { id: "BUS_008", route: "Route 419", status: "Active", cameraStatus: "Active", lat: 28.6339, lng: 77.2490, traffic: "High", lastUpdate: new Date(Date.now() - 90000).toISOString() }
];

export const events = [
  {
    event_id: "EVT_001",
    event_type: "pothole",
    confidence: 0.92,
    severity: "high",
    bus_id: "BUS_021",
    camera_id: "CAM_FRONT",
    latitude: 28.5639,
    longitude: 77.2090,
    timestamp: new Date(Date.now() - 120000).toISOString(),
    evidence: "https://images.unsplash.com/photo-1515162816999-a0c47dc192f7?auto=format&fit=crop&q=80&w=400",
    status: "new",
    repeated_detections: 6
  },
  {
    event_id: "EVT_002",
    event_type: "congestion",
    confidence: 0.95,
    severity: "high",
    bus_id: "BUS_014",
    camera_id: "CAM_FRONT",
    latitude: 28.6239,
    longitude: 77.2290,
    timestamp: new Date(Date.now() - 300000).toISOString(),
    evidence: "https://images.unsplash.com/photo-1502877338535-766e1452684a?auto=format&fit=crop&q=80&w=400",
    status: "verified",
    repeated_detections: 1
  },
  {
    event_id: "EVT_003",
    event_type: "road_defect",
    confidence: 0.89,
    severity: "medium",
    bus_id: "BUS_032",
    camera_id: "CAM_FRONT",
    latitude: 28.6139,
    longitude: 77.2090,
    timestamp: new Date(Date.now() - 540000).toISOString(),
    evidence: "https://images.unsplash.com/photo-1515162816999-a0c47dc192f7?auto=format&fit=crop&q=80&w=400",
    status: "under_review",
    repeated_detections: 3
  },
  {
    event_id: "EVT_004",
    event_type: "pothole",
    confidence: 0.78,
    severity: "low",
    bus_id: "BUS_045",
    camera_id: "CAM_FRONT",
    latitude: 28.5739,
    longitude: 77.2190,
    timestamp: new Date(Date.now() - 1800000).toISOString(),
    evidence: "https://images.unsplash.com/photo-1515162816999-a0c47dc192f7?auto=format&fit=crop&q=80&w=400",
    status: "new",
    repeated_detections: 1
  },
  {
    event_id: "EVT_005",
    event_type: "congestion",
    confidence: 0.88,
    severity: "medium",
    bus_id: "BUS_008",
    camera_id: "CAM_FRONT",
    latitude: 28.6339,
    longitude: 77.2490,
    timestamp: new Date(Date.now() - 7200000).toISOString(),
    evidence: "https://images.unsplash.com/photo-1502877338535-766e1452684a?auto=format&fit=crop&q=80&w=400",
    status: "resolved",
    repeated_detections: 2
  }
];

export const kpiMetrics = {
  activeBuses: 24,
  eventsToday: 134,
  potholesDetected: 42,
  trafficHotspots: 8,
  criticalAlerts: 3
};

export const trafficData = {
  densityOverTime: [
    { time: '06:00', density: 20 },
    { time: '08:00', density: 60 },
    { time: '10:00', density: 85 },
    { time: '12:00', density: 50 },
    { time: '14:00', density: 45 },
    { time: '16:00', density: 70 },
    { time: '18:00', density: 95 },
    { time: '20:00', density: 40 },
  ],
  vehicleTypes: [
    { name: 'Cars', value: 4500 },
    { name: 'Bikes', value: 3200 },
    { name: 'Buses', value: 800 },
    { name: 'Trucks', value: 450 },
  ],
  routes: [
    { id: 'Route 534', delay: '14 min', density: 'HIGH' },
    { id: 'Route 419', delay: '8 min', density: 'MEDIUM' },
    { id: 'Route 720', delay: '2 min', density: 'LOW' },
    { id: 'Route 312', delay: '5 min', density: 'MEDIUM' },
  ]
};

export const roadConditionData = {
  severityDistribution: [
    { name: 'High Severity', value: 12 },
    { name: 'Medium Severity', value: 24 },
    { name: 'Low Severity', value: 48 },
  ],
  defectsOverTime: [
    { day: 'Mon', newDefects: 12, resolved: 4 },
    { day: 'Tue', newDefects: 8, resolved: 6 },
    { day: 'Wed', newDefects: 15, resolved: 8 },
    { day: 'Thu', newDefects: 5, resolved: 12 },
    { day: 'Fri', newDefects: 9, resolved: 15 },
    { day: 'Sat', newDefects: 3, resolved: 5 },
    { day: 'Sun', newDefects: 2, resolved: 8 },
  ]
};

export const systemAlerts = [
  {
    id: "ALT_001",
    severity: "critical",
    message: "High congestion detected",
    source: "BUS_021",
    details: "Ring Road intersection",
    timestamp: new Date(Date.now() - 120000).toISOString()
  },
  {
    id: "ALT_002",
    severity: "high",
    message: "Persistent pothole detected",
    source: "6 buses observed",
    details: "Multiple verifications",
    timestamp: new Date(Date.now() - 480000).toISOString()
  },
  {
    id: "ALT_003",
    severity: "medium",
    message: "New road defect detected",
    source: "BUS_017",
    details: "Sector 14 Main Road",
    timestamp: new Date(Date.now() - 720000).toISOString()
  }
];
