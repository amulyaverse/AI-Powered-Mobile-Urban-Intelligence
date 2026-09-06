"""
routers/videos.py
-----------------
Serves sample road condition and pothole test videos from PR #37 (Pothole_Road_Condition_Model)
with HTTP range request streaming for browser <video> players and live inference feeder.
"""

from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter(prefix="/api/videos", tags=["Videos"])

PROJECT_ROOT = Path(__file__).resolve().parents[3]
POTHOLE_VIDEOS_DIR = PROJECT_ROOT / "edge-ai" / "Pothole_Road_Condition_Model"

SAMPLE_VIDEOS = [
    {
        "id": "cityRoad_potHoles.mp4",
        "title": "City Road Potholes (Front Angle)",
        "filename": "cityRoad_potHoles.mp4",
        "category": "road_defect",
        "description": "Urban street footage with road surface potholes and asphalt defects (PR #37).",
        "recommended_mode": "pothole",
        "source": "Pothole_Road_Condition_Model",
    },
    {
        "id": "cityRoad_potHoles-side.mp4",
        "title": "City Road Potholes (Side View)",
        "filename": "cityRoad_potHoles-side.mp4",
        "category": "road_defect",
        "description": "Angled urban perspective capturing road defect edges and depth contours.",
        "recommended_mode": "pothole",
        "source": "Pothole_Road_Condition_Model",
    },
    {
        "id": "ruralRoad_potHoles.mp4",
        "title": "Rural Road Severe Defects",
        "filename": "ruralRoad_potHoles.mp4",
        "category": "road_defect",
        "description": "Unpaved and broken asphalt road sections showing high-severity road damage.",
        "recommended_mode": "pothole",
        "source": "Pothole_Road_Condition_Model",
    },
]


@router.get("/samples")
def list_sample_videos():
    """
    List available sample videos from PR #37 for browser testing and live camera simulation.
    """
    samples = []
    for sample in SAMPLE_VIDEOS:
        file_path = POTHOLE_VIDEOS_DIR / sample["filename"]
        samples.append({
            **sample,
            "available": file_path.exists(),
            "size_bytes": file_path.stat().st_size if file_path.exists() else 0,
            "stream_url": f"/api/videos/stream/{sample['filename']}",
        })
    return samples


@router.get("/stream/{filename}")
def stream_sample_video(filename: str):
    """
    Stream a sample MP4 video with HTTP 206 Range request support.
    """
    safe_filename = Path(filename).name
    file_path = POTHOLE_VIDEOS_DIR / safe_filename

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail=f"Sample video '{safe_filename}' not found.")

    return FileResponse(
        path=str(file_path),
        media_type="video/mp4",
        filename=safe_filename,
    )
