# System Architecture

## High-Level Flow

```text
Camera / Video
      ↓
Edge AI
      ↓
Vehicle Detection + Pothole Detection
      ↓
Event Generation
      ↓
GPS + Timestamp + Confidence
      ↓
Network
      ↓
Backend API
      ↓
Database
      ↓
GIS Dashboard + Analytics
      ↓
Authority Action
```

## Components Description

1. **Edge Processing**: High-definition video streams are captured by bus-mounted cameras and fed into an onboard Edge AI device. The edge device runs lightweight object detection and classification models to identify road defects (potholes) and traffic density (vehicle counting).
2. **Event Generation**: When a significant entity is detected, the system generates an event. This involves bundling the detection data with contextual metadata, specifically the GPS coordinates, a timestamp, and the AI model's confidence score.
3. **Network Transmission**: Instead of streaming raw video, the edge device transmits only the structured, lightweight JSON events (along with optional compressed evidence images) over 4G/5G networks. This dramatically reduces bandwidth costs and latency.
4. **Centralized Aggregation (Backend)**: A cloud-based backend API receives incoming events from the entire fleet of buses. It validates, processes, and stores the events in a centralized database.
5. **GIS Visualization (Dashboard)**: The frontend application pulls aggregated data from the backend to display real-time and historical analytics on a map. Authorities can view heatmaps of pothole severity, traffic congestion, and track individual bus reporting.
