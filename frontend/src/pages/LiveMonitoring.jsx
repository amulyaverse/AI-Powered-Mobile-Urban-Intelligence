/**
 * LiveMonitoring.jsx
 * -------------------
 * Real-time fleet monitoring dashboard page with interactive camera feed integration.
 *
 * Layout:
 *   Left panel  — Active bus fleet list (polls REST /api/buses every 10 s)
 *   Right panel — Selected bus telemetry + Interactive Camera Feeder (Webcam, Video upload, External)
 *
 * Features:
 *   - Direct in-browser testing: captures webcam or video frames at 2 FPS
 *   - Sends binary JPEG frames over WebSocket to: ws://localhost:8000/api/ws/camera/{bus_id}
 *   - Renders live YOLO bounding boxes & detection labels directly over the camera feed
 *   - Real-time HUD showing FPS, sent frames, RTT latency, and vehicle/defect counts
 *   - Listens to broadcasted dashboard events via useEventWebSocket
 */

import React, { useEffect, useState, useCallback, useRef } from 'react';
import { getBuses, getWsUrl, getSampleVideos, API_BASE_URL } from '../services/api';
import { useEventWebSocket } from '../hooks/useEventWebSocket';
import LiveEventTicker from '../components/LiveEventTicker';
import { LoadingState, ErrorState } from '../components/PageStatusState';
import {
  Video,
  VideoOff,
  Camera,
  Upload,
  Play,
  Square,
  SignalHigh,
  Wifi,
  WifiOff,
  AlertCircle,
  CheckCircle2,
  MapPin,
  Cpu,
  Activity,
  Car,
  Layers,
  Sparkles,
  Clock,
} from 'lucide-react';
import { formatRelativeTime } from '../utils/dateTime';
import { format } from 'date-fns';

// ── Helpers ───────────────────────────────────────────────────────────────────
function formatTimeAgo(dateStr) {
  return formatRelativeTime(dateStr);
}

function filterEventsForBus(events, busId) {
  if (!busId) return events;
  return events.filter((e) => !e.bus_id || e.bus_id === busId);
}

// ── Main component ────────────────────────────────────────────────────────────
export default function LiveMonitoring() {
  const [buses, setBuses] = useState([]);
  const [selectedBus, setSelectedBus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [liveClock, setLiveClock] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setLiveClock(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  // Global broadcast WS
  const { isConnected: isBroadcastConnected, eventHistory, wsStatus } = useEventWebSocket();

  // ── Camera / Streamer State ──────────────────────────────────────────────────
  const [streamSource, setStreamSource] = useState('webcam'); // 'webcam' | 'video' | 'external'
  const [inferenceMode, setInferenceMode] = useState('traffic'); // 'traffic' | 'pothole'
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamStatus, setStreamStatus] = useState('Standby'); // 'Streaming' | 'Connecting' | 'Standby' | 'Error'
  const [streamFps, setStreamFps] = useState(0);
  const [framesSent, setFramesSent] = useState(0);
  const [latestLatencyMs, setLatestLatencyMs] = useState(null);
  const [lastDetections, setLastDetections] = useState([]);
  const [lastDetectionSummary, setLastDetectionSummary] = useState(null);
  const [cameraError, setCameraError] = useState(null);
  const [videoFileUrl, setVideoFileUrl] = useState(null);
  const [sampleVideos, setSampleVideos] = useState([]);
  const [selectedPresetId, setSelectedPresetId] = useState('cityRoad_potHoles.mp4');

  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const hiddenCanvasRef = useRef(null);
  const streamWsRef = useRef(null);
  const streamIntervalRef = useRef(null);
  const mediaStreamRef = useRef(null);
  const frameCountWindowRef = useRef(0);
  const fpsIntervalRef = useRef(null);
  const isStreamingRef = useRef(false);
  const lastFrameSentTimeRef = useRef(0);

  // Load sample test videos from PR 37
  useEffect(() => {
    getSampleVideos()
      .then((vids) => {
        if (Array.isArray(vids) && vids.length > 0) {
          setSampleVideos(vids);
          const first = vids[0];
          if (first && !videoFileUrl) {
            setVideoFileUrl(`${API_BASE_URL}${first.stream_url}`);
            setSelectedPresetId(first.id);
          }
        }
      })
      .catch((err) => console.warn('[LiveMonitoring] Failed to fetch sample videos:', err));
  }, []);

  const handleSelectPreset = (video) => {
    setSelectedPresetId(video.id);
    setVideoFileUrl(`${API_BASE_URL}${video.stream_url}`);
    if (video.recommended_mode && video.recommended_mode !== inferenceMode) {
      setInferenceMode(video.recommended_mode);
    }
  };

  // Load bus fleet list
  const loadBuses = useCallback(async (isInitial = false) => {
    if (isInitial) setLoading(true);
    try {
      const data = await getBuses();
      const safeBuses = Array.isArray(data) ? data : [];
      setBuses(safeBuses);
      if (safeBuses.length > 0) {
        setSelectedBus((prev) =>
          prev ? safeBuses.find((b) => b.id === prev.id) || safeBuses[0] : safeBuses[0]
        );
      }
      setError(null);
    } catch (err) {
      console.error('[LiveMonitoring] Failed to load buses:', err);
      setError(err.message || 'Failed to load fleet telemetry.');
    } finally {
      if (isInitial) setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadBuses(true);
    const interval = setInterval(() => loadBuses(false), 4_000);
    return () => clearInterval(interval);
  }, [loadBuses]);

  // Clean up streaming when unmounting
  useEffect(() => {
    return () => {
      stopCameraStream();
    };
  }, []);

  // ── Draw bounding boxes onto canvas overlay ──────────────────────────────────
  const drawBoxes = useCallback((detections, videoEl, canvasEl) => {
    if (!canvasEl || !videoEl) return;
    const ctx = canvasEl.getContext('2d');
    if (!ctx) return;

    // Match canvas display size to video display size
    const rect = videoEl.getBoundingClientRect();
    if (rect.width === 0 || rect.height === 0) return;

    canvasEl.width = rect.width;
    canvasEl.height = rect.height;
    ctx.clearRect(0, 0, canvasEl.width, canvasEl.height);

    if (!detections || detections.length === 0) return;

    // Inferences were performed on standard 640x480 frame
    const scaleX = canvasEl.width / 640;
    const scaleY = canvasEl.height / 480;

    detections.forEach((det) => {
      let bx1 = 0, by1 = 0, bx2 = 0, by2 = 0;
      if (Array.isArray(det.bbox)) {
        [bx1, by1, bx2, by2] = det.bbox;
      } else if (Array.isArray(det.bounding_box)) {
        [bx1, by1, bx2, by2] = det.bounding_box;
      } else if (det.x1 != null && det.y1 != null) {
        bx1 = det.x1; by1 = det.y1; bx2 = det.x2; by2 = det.y2;
      } else if (Array.isArray(det) && det.length >= 4) {
        [bx1, by1, bx2, by2] = det;
      }

      const x = bx1 * scaleX;
      const y = by1 * scaleY;
      const w = Math.max(12, (bx2 - bx1) * scaleX);
      const h = Math.max(12, (by2 - by1) * scaleY);

      const cls = (det.class || det.label || det.type || 'pothole').toLowerCase();
      const conf = det.conf != null ? Math.round(det.conf * 100) : (det.confidence != null ? Math.round(det.confidence * 100) : null);

      const isAlert = cls.includes('pothole') || cls.includes('defect') || cls.includes('crack') || cls.includes('severe');
      const boxColor = isAlert ? '#ef4444' : '#10b981';
      const bgColor = isAlert ? 'rgba(239, 68, 68, 0.90)' : 'rgba(16, 185, 129, 0.90)';

      // Box outline
      ctx.strokeStyle = boxColor;
      ctx.lineWidth = 2.5;
      ctx.shadowColor = boxColor;
      ctx.shadowBlur = 6;
      ctx.strokeRect(x, y, w, h);
      ctx.shadowBlur = 0;

      // Label badge
      const label = `${cls.toUpperCase()}${conf != null ? ` ${conf}%` : ''}`;
      ctx.font = 'bold 11px sans-serif';
      const textWidth = ctx.measureText(label).width;
      const badgeHeight = 18;

      ctx.fillStyle = bgColor;
      ctx.fillRect(x, Math.max(0, y - badgeHeight), textWidth + 8, badgeHeight);

      ctx.fillStyle = '#ffffff';
      ctx.fillText(label, x + 4, Math.max(12, y - 4));
    });
  }, []);

  // ── Stop Camera Stream ───────────────────────────────────────────────────────
  const stopCameraStream = useCallback(() => {
    isStreamingRef.current = false;
    setIsStreaming(false);
    setStreamStatus('Standby');
    setStreamFps(0);

    if (streamIntervalRef.current) {
      clearInterval(streamIntervalRef.current);
      streamIntervalRef.current = null;
    }
    if (fpsIntervalRef.current) {
      clearInterval(fpsIntervalRef.current);
      fpsIntervalRef.current = null;
    }
    if (streamWsRef.current) {
      try {
        streamWsRef.current.close();
      } catch { /* ignore */ }
      streamWsRef.current = null;
    }
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((track) => track.stop());
      mediaStreamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.pause();
      videoRef.current.srcObject = null;
    }
    if (canvasRef.current) {
      const ctx = canvasRef.current.getContext('2d');
      if (ctx) ctx.clearRect(0, 0, canvasRef.current.width, canvasRef.current.height);
    }
  }, []);

  // ── Start Camera Stream ─────────────────────────────────────────────────────
  const startCameraStream = async () => {
    setCameraError(null);
    setLastDetections([]);
    setLastDetectionSummary(null);
    setFramesSent(0);

    const busId = selectedBus?.id || 'BUS_021';
    const lat = selectedBus?.last_lat ?? selectedBus?.lat ?? 28.6139;
    const lng = selectedBus?.last_lng ?? selectedBus?.lng ?? 77.2090;

    setStreamStatus('Connecting');

    // 1. Prepare video source
    try {
      if (streamSource === 'webcam') {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { width: { ideal: 640 }, height: { ideal: 480 }, frameRate: { ideal: 15 } },
          audio: false,
        });
        mediaStreamRef.current = stream;
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          await videoRef.current.play();
        }
      } else if (streamSource === 'video') {
        if (!videoFileUrl) {
          setCameraError('Please upload or select an MP4 video file first.');
          setStreamStatus('Error');
          return;
        }
        if (videoRef.current) {
          videoRef.current.crossOrigin = 'anonymous';
          videoRef.current.src = videoFileUrl;
          videoRef.current.loop = true;
          videoRef.current.muted = true;
          await videoRef.current.play();
        }
      }
    } catch (err) {
      console.error('[LiveMonitoring] Media stream error:', err);
      setCameraError(`Camera access denied or unavailable: ${err.message}`);
      setStreamStatus('Error');
      return;
    }

    // 2. Connect WebSocket to backend camera ingestion endpoint
    const wsUrl = getWsUrl(`/api/ws/camera/${busId}?lat=${lat}&lng=${lng}&mode=${inferenceMode}`);
    let ws;
    try {
      ws = new WebSocket(wsUrl);
      ws.binaryType = 'blob';
      streamWsRef.current = ws;
    } catch (wsErr) {
      setCameraError(`Failed to connect to camera WebSocket: ${wsErr.message}`);
      setStreamStatus('Error');
      return;
    }

    ws.onopen = () => {
      setStreamStatus('Streaming');
      setIsStreaming(true);
      isStreamingRef.current = true;
      frameCountWindowRef.current = 0;

      // Start FPS counter
      fpsIntervalRef.current = setInterval(() => {
        setStreamFps(frameCountWindowRef.current);
        frameCountWindowRef.current = 0;
      }, 1000);

      // 3. Start 2 FPS frame capture loop (every 500 ms)
      streamIntervalRef.current = setInterval(() => {
        if (!isStreamingRef.current || !videoRef.current || ws.readyState !== WebSocket.OPEN) return;

        const video = videoRef.current;
        if (video.videoWidth === 0 || video.videoHeight === 0) return;

        // Draw frame onto offscreen canvas (640x480)
        let offscreenCanvas = hiddenCanvasRef.current;
        if (!offscreenCanvas) {
          offscreenCanvas = document.createElement('canvas');
          offscreenCanvas.width = 640;
          offscreenCanvas.height = 480;
          hiddenCanvasRef.current = offscreenCanvas;
        }
        const ctx = offscreenCanvas.getContext('2d');
        ctx.drawImage(video, 0, 0, 640, 480);

        offscreenCanvas.toBlob(
          (blob) => {
            if (blob && ws.readyState === WebSocket.OPEN) {
              lastFrameSentTimeRef.current = performance.now();
              ws.send(blob);
              frameCountWindowRef.current += 1;
              setFramesSent((prev) => prev + 1);
            }
          },
          'image/jpeg',
          0.8
        );
      }, 500); // 2 FPS
    };

    ws.onmessage = (event) => {
      try {
        if (lastFrameSentTimeRef.current > 0) {
          setLatestLatencyMs(Math.round(performance.now() - lastFrameSentTimeRef.current));
        }

        const data = JSON.parse(event.data);
        if (data.status === 'frame_skipped') return;
        if (data.status === 'suppressed' && !data.boxes && !data.detections) return;

        if (data.status === 'no_detection') {
          setLastDetections([]);
          setLastDetectionSummary({ status: 'clear', message: '0 detections (Clear)' });
          if (canvasRef.current && videoRef.current) {
            drawBoxes([], videoRef.current, canvasRef.current);
          }
          return;
        }

        // Detections returned
        const boxes = data.detections || data.boxes || [];
        setLastDetections(boxes);
        setLastDetectionSummary(data);

        if (canvasRef.current && videoRef.current) {
          drawBoxes(boxes, videoRef.current, canvasRef.current);
        }
      } catch (err) {
        console.warn('[LiveMonitoring] Parse server detection error:', err);
      }
    };

    ws.onerror = (err) => {
      console.error('[LiveMonitoring] Camera WS error:', err);
      setCameraError('Camera stream connection failed.');
      setStreamStatus('Error');
    };

    ws.onclose = () => {
      if (isStreamingRef.current) {
        setStreamStatus('Standby');
        stopCameraStream();
      }
    };
  };

  const handleVideoFileUpload = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      const url = URL.createObjectURL(file);
      setVideoFileUrl(url);
    }
  };

  // Derive events relevant to selected bus
  const busEvents = filterEventsForBus(eventHistory, selectedBus?.id);
  const latestBusEvent = busEvents[0] || null;

  if (loading && buses.length === 0) {
    return <LoadingState message="Connecting to live bus fleet telemetry..." />;
  }

  if (error && buses.length === 0) {
    return (
      <ErrorState
        title="Fleet Telemetry Unavailable"
        message={error}
        onRetry={() => loadBuses(true)}
      />
    );
  }

  const currentLat = selectedBus?.last_lat ?? selectedBus?.lat;
  const currentLng = selectedBus?.last_lng ?? selectedBus?.lng;
  const currentTraffic = selectedBus?.last_traffic || selectedBus?.traffic || 'Normal';

  return (
    <div className="flex flex-col h-full gap-6">
      {/* ── Top Bar ────────────────────────────────────────────────────────── */}
      <div className="flex justify-between items-center bg-white p-4 rounded-lg shadow-xs border border-slate-200">
        <div>
          <h2 className="text-xl font-bold text-slate-800 flex items-center gap-2">
            <Video className="w-5 h-5 text-blue-600" />
            Live Urban Fleet & Edge AI Monitoring
          </h2>
          <p className="text-sm text-slate-500">
            Real-time multi-bus telemetry, server-side YOLO inference stream, and spatial anomaly aggregation
          </p>
        </div>

        <div className="flex items-center gap-3">
          {isBroadcastConnected ? (
            <div className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
              <Wifi className="w-3.5 h-3.5" />
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              Broadcast WS Online · {eventHistory.length} events
            </div>
          ) : (
            <div className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200">
              <WifiOff className="w-3.5 h-3.5" />
              Reconnecting to Event WS…
            </div>
          )}
        </div>
      </div>

      {/* ── Main Layout: Split Screen ───────────────────────────────────────── */}
      <div className="flex flex-1 gap-6 overflow-hidden min-h-0">
        {/* ── Left: Active Buses List ───────────────────────────────────────── */}
        <div className="w-80 bg-white rounded-lg shadow-xs border border-slate-200 flex flex-col shrink-0">
          <div className="p-4 border-b border-slate-200 flex justify-between items-center bg-slate-50">
            <h3 className="font-semibold text-slate-700 text-sm">Active Fleet Units</h3>
            <span className="text-xs bg-blue-100 text-blue-700 font-medium px-2 py-0.5 rounded-full">
              {buses.length} online
            </span>
          </div>

          <div className="p-3 border-b border-slate-100 bg-white">
            <p className="text-xs text-slate-500">
              Click a unit to attach its live stream and telemetry context:
            </p>
          </div>

          <div className="flex-1 overflow-y-auto divide-y divide-slate-100">
            {buses.length === 0 ? (
              <div className="p-6 text-center text-slate-400 text-sm">No buses reporting</div>
            ) : (
              buses.map((bus) => {
                const isSelected = selectedBus?.id === bus.id;
                const busTraffic = bus.last_traffic || bus.traffic || 'Normal';
                const isHighTraffic = busTraffic === 'Heavy' || busTraffic === 'Congested';
                return (
                  <button
                    key={bus.id}
                    onClick={() => {
                      if (isStreaming) stopCameraStream();
                      setSelectedBus(bus);
                    }}
                    className={`w-full text-left p-3.5 transition-colors flex flex-col gap-1.5 cursor-pointer ${
                      isSelected
                        ? 'bg-blue-50/80 border-l-4 border-blue-600'
                        : 'hover:bg-slate-50 border-l-4 border-transparent'
                    }`}
                  >
                    <div className="flex justify-between items-center">
                      <span className="font-bold text-sm text-slate-800">{bus.id}</span>
                      <span
                        className={`text-xs px-2 py-0.5 rounded font-medium ${
                          isHighTraffic
                            ? 'bg-amber-100 text-amber-800'
                            : 'bg-emerald-100 text-emerald-800'
                        }`}
                      >
                        {busTraffic}
                      </span>
                    </div>
                    <div className="text-xs text-slate-500 flex items-center justify-between">
                      <span className="flex items-center gap-1 font-mono">
                        <MapPin className="w-3 h-3 text-slate-400" />
                        {bus.route || 'Patrol Unit'}
                      </span>
                      <span className="flex items-center gap-1">
                        <SignalHigh className="w-3 h-3 text-slate-400" />
                        {formatTimeAgo(bus.last_seen || bus.lastUpdate)}
                      </span>
                    </div>
                  </button>
                );
              })
            )}
          </div>
        </div>

        {/* ── Right: Selected Bus & Interactive Camera Feed ─────────────────── */}
        {selectedBus && (
          <div className="flex-1 bg-white rounded-lg shadow-xs border border-slate-200 flex flex-col overflow-hidden">
            {/* Bus header */}
            <div className="p-4 border-b border-slate-200 bg-slate-50 flex justify-between items-center shrink-0">
              <div>
                <h3 className="font-bold text-lg text-slate-800 flex items-center gap-2">
                  <span>{selectedBus.id}</span>
                  <span className="text-xs font-normal px-2.5 py-0.5 rounded-full bg-slate-200 text-slate-700">
                    {selectedBus.route || 'Route 12'}
                  </span>
                </h3>
                <p className="text-xs text-slate-500 font-mono mt-0.5">
                  GPS: {currentLat != null ? `${currentLat.toFixed(4)}, ${currentLng?.toFixed(4)}` : 'N/A'}
                </p>
              </div>

              {/* Source & Mode Selection Controls */}
              <div className="flex items-center gap-3">
                {/* Mode Selector */}
                <div className="flex items-center bg-slate-200 rounded-lg p-0.5 text-xs font-medium">
                  <button
                    onClick={() => {
                      if (isStreaming) stopCameraStream();
                      setInferenceMode('traffic');
                    }}
                    className={`px-2.5 py-1 rounded-md transition-colors cursor-pointer ${
                      inferenceMode === 'traffic'
                        ? 'bg-white text-blue-700 shadow-2xs font-semibold'
                        : 'text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    Traffic (Vehicles)
                  </button>
                  <button
                    onClick={() => {
                      if (isStreaming) stopCameraStream();
                      setInferenceMode('pothole');
                    }}
                    className={`px-2.5 py-1 rounded-md transition-colors cursor-pointer ${
                      inferenceMode === 'pothole'
                        ? 'bg-white text-amber-700 shadow-2xs font-semibold'
                        : 'text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    Potholes (Defects)
                  </button>
                </div>

                {/* Source Selector */}
                <div className="flex items-center bg-slate-200 rounded-lg p-0.5 text-xs font-medium">
                  <button
                    onClick={() => {
                      if (isStreaming) stopCameraStream();
                      setStreamSource('webcam');
                    }}
                    className={`flex items-center gap-1 px-2.5 py-1 rounded-md transition-colors cursor-pointer ${
                      streamSource === 'webcam'
                        ? 'bg-white text-slate-900 shadow-2xs font-semibold'
                        : 'text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    <Camera className="w-3.5 h-3.5" />
                    Webcam
                  </button>
                  <button
                    onClick={() => {
                      if (isStreaming) stopCameraStream();
                      setStreamSource('video');
                    }}
                    className={`flex items-center gap-1 px-2.5 py-1 rounded-md transition-colors cursor-pointer ${
                      streamSource === 'video'
                        ? 'bg-white text-slate-900 shadow-2xs font-semibold'
                        : 'text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    <Upload className="w-3.5 h-3.5" />
                    Video File
                  </button>
                </div>

                {/* Start / Stop Stream Button */}
                {isStreaming ? (
                  <button
                    onClick={stopCameraStream}
                    className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-bold bg-red-600 text-white hover:bg-red-700 shadow-2xs transition-colors cursor-pointer"
                  >
                    <Square className="w-3.5 h-3.5 fill-current" />
                    Stop Stream
                  </button>
                ) : (
                  <button
                    onClick={startCameraStream}
                    className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-bold bg-emerald-600 text-white hover:bg-emerald-700 shadow-2xs transition-colors cursor-pointer"
                  >
                    <Play className="w-3.5 h-3.5 fill-current" />
                    Start Camera Feed
                  </button>
                )}
              </div>
            </div>

            {/* Main view area */}
            <div className="p-4 flex-1 flex flex-col gap-4 overflow-y-auto">
              {/* PR #37 Sample Video Presets & Upload Bar */}
              {streamSource === 'video' && !isStreaming && (
                <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-lg text-xs space-y-2.5">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-slate-800 flex items-center gap-1.5">
                        <Sparkles className="w-3.5 h-3.5 text-amber-600" />
                        PR #37 Road Condition & Pothole Video Feeds:
                      </span>
                      <span className="text-[10px] bg-amber-100 text-amber-800 px-2 py-0.5 rounded-full font-semibold">
                        Pothole_Road_Condition_Model
                      </span>
                    </div>
                    <span className="text-slate-400 text-[11px]">Select a video feed to test live</span>
                  </div>

                  <div className="flex flex-wrap gap-2">
                    {sampleVideos.map((video) => {
                      const isSelected = selectedPresetId === video.id || videoFileUrl?.includes(video.filename);
                      return (
                        <button
                          key={video.id}
                          type="button"
                          onClick={() => handleSelectPreset(video)}
                          className={`px-3 py-1.5 rounded-md border text-xs font-semibold flex items-center gap-1.5 transition-all cursor-pointer ${
                            isSelected
                              ? 'bg-amber-600 text-white border-amber-600 shadow-xs'
                              : 'bg-white text-slate-700 border-slate-300 hover:border-amber-500 hover:bg-amber-50/50'
                          }`}
                        >
                          <span>{video.title}</span>
                          <span className={`text-[10px] px-1.5 py-0.5 rounded font-mono ${isSelected ? 'bg-amber-700 text-white' : 'bg-slate-100 text-slate-500'}`}>
                            {video.filename}
                          </span>
                        </button>
                      );
                    })}
                  </div>

                  <div className="flex items-center gap-3 pt-2 border-t border-slate-200/70 text-slate-500">
                    <Upload className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                    <span className="font-medium text-slate-600">Or upload custom road/traffic video:</span>
                    <input
                      type="file"
                      accept="video/mp4,video/webm"
                      onChange={handleVideoFileUpload}
                      className="text-xs text-slate-600 file:mr-2 file:py-0.5 file:px-2 file:rounded file:border-0 file:text-[11px] file:font-semibold file:bg-slate-700 file:text-white hover:file:bg-slate-800 cursor-pointer"
                    />
                    {videoFileUrl && <span className="text-emerald-600 font-semibold ml-auto flex items-center gap-1"><CheckCircle2 className="w-3.5 h-3.5" /> Video Ready</span>}
                  </div>
                </div>
              )}

              {/* Error Banner */}
              {cameraError && (
                <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700">
                  <AlertCircle className="w-4 h-4 text-red-600 shrink-0" />
                  <span>{cameraError}</span>
                </div>
              )}

              {/* ── Live Video & Inference Overlay Viewport ───────────────────── */}
              <div className="bg-slate-950 rounded-xl relative overflow-hidden border border-slate-800 shadow-inner flex items-center justify-center min-h-[360px] aspect-video">
                {/* HUD Top Bar */}
                <div className="absolute top-0 inset-x-0 flex items-center justify-between px-4 py-2.5 bg-gradient-to-b from-black/80 to-transparent z-20">
                  <div className="flex items-center gap-2">
                    <span
                      className={`text-[11px] px-2 py-0.5 rounded uppercase font-bold flex items-center gap-1.5 ${
                        isStreaming
                          ? 'bg-red-500 text-white animate-pulse'
                          : 'bg-slate-700 text-slate-300'
                      }`}
                    >
                      <span className={`w-1.5 h-1.5 rounded-full ${isStreaming ? 'bg-white' : 'bg-slate-400'}`} />
                      {isStreaming ? 'LIVE INGESTION' : 'STANDBY'}
                    </span>
                    <span className="bg-black/60 text-white font-mono text-[11px] px-2 py-0.5 rounded border border-white/10">
                      {selectedBus.id} · CAM_FRONT
                    </span>
                    <span className="bg-blue-600/80 text-white text-[10px] px-2 py-0.5 rounded font-semibold uppercase">
                      {inferenceMode}
                    </span>
                  </div>

                  {/* Telemetry HUD right */}
                  <div className="flex items-center gap-2 text-white font-mono text-xs">
                    <div className="bg-black/60 px-2.5 py-1 rounded border border-white/10 flex items-center gap-1.5 text-slate-200">
                      <Clock className="w-3 h-3 text-cyan-400 animate-pulse" />
                      <span>{format(liveClock, 'HH:mm:ss')}</span>
                    </div>
                    {isStreaming && (
                      <>
                        <div className="bg-black/60 px-2.5 py-1 rounded border border-white/10 flex items-center gap-1.5">
                          <Activity className="w-3 h-3 text-emerald-400" />
                          <span>{streamFps} FPS</span>
                        </div>
                        <div className="bg-black/60 px-2.5 py-1 rounded border border-white/10">
                          Frames: {framesSent}
                        </div>
                      </>
                    )}
                    {currentLat != null && (
                      <div className="bg-black/60 px-2.5 py-1 rounded border border-white/10 flex items-center gap-1">
                        <MapPin className="w-3 h-3 text-blue-400" />
                        {currentLat.toFixed(4)}, {currentLng?.toFixed(4)}
                      </div>
                    )}
                  </div>
                </div>

                {/* HTML Video Element */}
                <video
                  ref={videoRef}
                  playsInline
                  muted
                  className={`w-full h-full object-contain ${isStreaming ? 'block' : 'hidden'}`}
                />

                {/* Bounding Box Overlay Canvas */}
                <canvas
                  ref={canvasRef}
                  className={`absolute inset-0 pointer-events-none z-10 w-full h-full ${isStreaming ? 'block' : 'hidden'}`}
                />

                {/* Standby Empty State (when not streaming) */}
                {!isStreaming && (
                  <div className="flex flex-col items-center justify-center p-8 text-center text-slate-400 z-10">
                    <div className="w-16 h-16 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center mb-3">
                      <Camera className="w-8 h-8 text-slate-500" />
                    </div>
                    <h4 className="text-base font-bold text-slate-200 mb-1">Camera Stream Inactive</h4>
                    <p className="text-xs text-slate-400 max-w-sm mb-4">
                      Click <strong>"Start Camera Feed"</strong> above to attach your laptop webcam or a test video file. Frames will stream at 2 FPS and YOLO will detect objects live.
                    </p>
                    <div className="flex items-center gap-2 text-[11px] text-slate-500 bg-slate-900/80 px-3 py-1.5 rounded-full border border-slate-800">
                      <span>Or stream via terminal:</span>
                      <code className="text-emerald-400 font-mono">python scripts/stream_camera.py --synthetic</code>
                    </div>
                  </div>
                )}

                {/* HUD Bottom Status Banner (when streaming) */}
                {isStreaming && (
                  <div className="absolute bottom-0 inset-x-0 px-4 py-2 bg-gradient-to-t from-black/90 to-transparent z-20 flex items-center justify-between text-xs text-white font-mono">
                    <div className="flex items-center gap-2 flex-wrap">
                      <Sparkles className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                      <span>
                        {lastDetectionSummary?.event_type
                          ? `Detection: ${lastDetectionSummary.event_type.toUpperCase()} (Conf: ${Math.round((lastDetectionSummary.confidence || 0) * 100)}%)`
                          : lastDetections.length > 0
                          ? `Defects Detected: ${lastDetections.length}`
                          : 'No incidents in view (Road surface clear)'}
                      </span>
                      {lastDetectionSummary?.width_ratio != null && (
                        <span className="bg-amber-500/30 text-amber-300 px-2 py-0.5 rounded border border-amber-500/40 text-[11px] font-bold">
                          PR #37 Width: {Math.round(lastDetectionSummary.width_ratio * 100)}% ({lastDetectionSummary.severity?.toUpperCase()})
                        </span>
                      )}
                      {lastDetectionSummary?.area_ratio != null && (
                        <span className="bg-blue-500/20 text-blue-300 px-2 py-0.5 rounded border border-blue-500/30 text-[11px]">
                          Area: {(lastDetectionSummary.area_ratio * 100).toFixed(2)}%
                        </span>
                      )}
                    </div>
                    {lastDetectionSummary?.density && (
                      <span className="text-emerald-400 font-bold shrink-0">
                        Traffic Density: {lastDetectionSummary.density}
                      </span>
                    )}
                  </div>
                )}
              </div>

              {/* Status Metric Cards */}
              <div className="grid grid-cols-3 gap-4">
                <div className="p-3.5 border border-slate-200 rounded-lg bg-slate-50 flex flex-col justify-between">
                  <p className="text-xs text-slate-500 font-medium">Telemetry GPS</p>
                  <p className="font-mono text-slate-800 text-sm font-semibold mt-1">
                    {currentLat != null ? `${currentLat.toFixed(4)}, ${currentLng?.toFixed(4)}` : 'No GPS data'}
                  </p>
                </div>

                <div className="p-3.5 border border-slate-200 rounded-lg bg-slate-50 flex flex-col justify-between">
                  <p className="text-xs text-slate-500 font-medium">Inference Engine</p>
                  <div className="text-slate-800 text-sm font-semibold mt-1 flex items-center gap-1.5">
                    <Cpu className="w-4 h-4 text-blue-600 shrink-0" />
                    <span>
                      {inferenceMode === 'pothole' ? 'YOLOv8 Road Defect AI (PR #37)' : 'YOLOv8 Edge (TRAFFIC)'}
                    </span>
                  </div>
                  {inferenceMode === 'pothole' && (
                    <span className="text-[10px] text-amber-700 font-medium mt-0.5">
                      Approach A Width Heuristic + Area Ratio
                    </span>
                  )}
                </div>

                <div className="p-3.5 border border-slate-200 rounded-lg bg-slate-50 flex flex-col justify-between">
                  <p className="text-xs text-slate-500 font-medium">Latest Incident</p>
                  {latestBusEvent ? (
                    <div className="font-semibold text-slate-800 flex items-center gap-1.5 text-sm mt-1">
                      <AlertCircle
                        className={`w-4 h-4 shrink-0 ${
                          latestBusEvent.severity === 'high' || latestBusEvent.severity === 'critical'
                            ? 'text-red-500'
                            : 'text-amber-500'
                        }`}
                      />
                      <span className="capitalize truncate">
                        {latestBusEvent.event_type.replace(/_/g, ' ')}
                      </span>
                      <span className="text-xs text-slate-400 font-normal">
                        ({formatTimeAgo(latestBusEvent.timestamp)})
                      </span>
                    </div>
                  ) : (
                    <p className="text-slate-600 flex items-center gap-1 text-sm font-medium mt-1">
                      <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                      No recent incidents
                    </p>
                  )}
                </div>
              </div>

              {/* Broadcast Live Event Ticker */}
              <div>
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">
                  Broadcast AI Detections · {selectedBus.id}
                </p>
                {busEvents.length > 0 ? (
                  <LiveEventTicker events={busEvents} maxVisible={4} />
                ) : (
                  <div className="p-4 border border-dashed border-slate-200 rounded-lg text-center text-slate-400 text-xs">
                    No detections registered yet. As frames are ingested, detected events will stream here live.
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
