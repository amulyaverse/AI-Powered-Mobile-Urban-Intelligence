# AI-Powered Mobile Urban Intelligence Platform

## Overview
Transforming public transport buses into mobile AI-powered urban sensing units. This platform uses edge AI to analyze video feeds from bus-mounted cameras, detecting critical road and traffic information, and providing authorities with real-time, geo-tagged events via a GIS-based dashboard.

## Problem Statement
City authorities lack real-time, granular data on road conditions and traffic congestion. Traditional sensing methods (static cameras, manual surveys) are expensive, have limited coverage, and cannot dynamically adapt to changing urban environments.

## Our Solution
We leverage the existing public transport fleet as a network of mobile sensors. By deploying edge computing devices and cameras on buses, we continuously monitor the city's infrastructure and traffic patterns without requiring vast new physical infrastructure.

## Why Use Public Buses as Mobile Sensors?
* **Extensive Coverage:** Buses travel across the entire city regularly.
* **Cost-Effective:** Utilizes existing vehicles instead of installing thousands of static sensors.
* **Continuous Monitoring:** Provides updated data multiple times a day on the same routes.
* **Proactive Maintenance:** Allows authorities to detect issues like potholes or congestion early.

## Core MVP
For the current SIH internal prototype, the core features include:
1. Vehicle detection, classification, and counting.
2. Traffic-density and congestion estimation.
3. Pothole and road-defect detection.
4. GPS, timestamp, and confidence-based event generation.
5. Centralized backend and database.
6. GIS dashboard with basic analytics and heatmaps.

## System Workflow
```text
Bus Camera
    ↓
Edge AI
    ↓
Detection
    ↓
Event Generation
    ↓
GPS + Timestamp + Confidence
    ↓
Backend API
    ↓
Database
    ↓
GIS Dashboard
    ↓
Authority Action
```

## System Architecture

*Note: For the SIH prototype, we use a laptop/PC as the simulated edge device since actual bus hardware is unavailable.*

### Prototype Architecture
```text
Recorded Video
    ↓
Laptop / PC
    ↓
AI inference
    ↓
Backend
    ↓
Dashboard
```

### Intended Deployment Architecture
```text
Bus Cameras
    ↓
Edge Compute Device
    ↓
4G/5G/Network
    ↓
Central Platform
```

## Edge AI Approach
All AI inference (object detection, classification) is run on the edge device to minimize bandwidth usage and latency. Only lightweight, structured metadata (geo-tagged events and evidence snippets) are sent over the network to the centralized backend.

## Technology Stack
*To be populated as modules are developed.*

## Project Structure
* **`edge-ai/`**: Traffic and pothole detection AI models.
* **`backend/`**: API, database configurations, and core models.
* **`frontend/`**: GIS map, analytics, and dashboard.
* **`integration/`**: Event generation and GPS tracking integration.
* **`datasets/`**: Placeholder for datasets used during development.
* **`docs/`**: Architecture diagrams, API schemas, and ML model details.

## Installation
*(Instructions for setting up the backend, frontend, and edge simulation environments will be added here.)*

## Usage
*(Instructions for running the end-to-end prototype will be added here.)*

## Demo
*(Links to videos or live demonstrations of the system.)*

## Live Deployment
*(Links to any live deployed dashboards or APIs.)*

## Results / Performance
*(Model metrics, latency stats, and overall system performance.)*

## Team
* **Pranav:** Traffic AI / Computer Vision
* **Abhinandan:** ML / Road-Damage AI
* **Arjun:** Backend / Database
* **Advika:** Frontend / GIS
* **Parminder:** Edge AI / Integration

## Future Scope
These features are planned for future expansion and are **NOT** part of the current MVP:
* Waterlogging detection
* Traffic-sign detection
* Missing zebra crossings/dividers detection
* Pedestrian-risk detection
* Rash driving detection
* ANPR (Automatic Number Plate Recognition)
* Hit-and-run incident reporting
* Origin–destination analysis
* Advanced route prediction

## SIH'26 Submission
*(Final submission details, links, and documents for the hackathon.)*
