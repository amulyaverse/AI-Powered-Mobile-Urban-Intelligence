"""
routers/videos.py
-----------------
Serves sample road condition and pothole test videos from PR #37 (Pothole_Road_Condition_Model)
with HTTP range request streaming for browser <video> players and live inference feeder.
"""

from pathlib import Path
from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/api/videos", tags=["Videos"])

PROJECT_ROOT = Path(__file__).resolve().parents[3]
VIDEO_SEARCH_DIRS = [
    PROJECT_ROOT / "frontend" / "public" / "videos",
    PROJECT_ROOT / "edge-ai" / "Pothole_Road_Condition_Model",
    PROJECT_ROOT / "edge-ai" / "pothole-latest" / "Pothole_Road_Condition_Model",
]
POTHOLE_VIDEOS_DIR = PROJECT_ROOT / "edge-ai" / "Pothole_Road_Condition_Model"
CHUNK_SIZE = 1024 * 512  # 512 KB

def resolve_video_path(filename: str) -> Path:
    safe_filename = Path(filename).name
    for directory in VIDEO_SEARCH_DIRS:
        cand = directory / safe_filename
        if cand.is_file() and cand.exists():
            return cand
    return POTHOLE_VIDEOS_DIR / safe_filename

SAMPLE_VIDEOS = [
    {
        "id": "153283-804933523.mp4",
        "title": "Traffic Congestion Feed",
        "filename": "153283-804933523.mp4",
        "category": "traffic",
        "description": "Traffic monitoring sample feed.",
        "recommended_mode": "traffic",
        "source": "User Provided",
    },
    {
        "id": "Potholes_detection.mp4",
        "title": "Potholes Detection Feed",
        "filename": "Potholes_detection.mp4",
        "category": "road_defect",
        "description": "Sample footage for pothole detection.",
        "recommended_mode": "pothole",
        "source": "User Provided",
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
        file_path = resolve_video_path(sample["filename"])
        is_avail = file_path.exists() and file_path.is_file()
        samples.append({
            **sample,
            "available": is_avail,
            "size_bytes": file_path.stat().st_size if is_avail else 0,
            "stream_url": f"/api/videos/stream/{sample['filename']}",
        })
    return samples


@router.get("/stream/{filename}")
def stream_sample_video(filename: str, request: Request):
    """
    Stream a sample MP4 video with HTTP 206 Partial Content Range request support for seeking.
    """
    safe_filename = Path(filename).name
    file_path = resolve_video_path(safe_filename)

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail=f"Sample video '{safe_filename}' not found.")

    file_size = file_path.stat().st_size
    range_header = request.headers.get("range")

    if not range_header:
        def iter_full_file():
            with open(file_path, "rb") as f:
                while chunk := f.read(CHUNK_SIZE):
                    yield chunk

        return StreamingResponse(
            iter_full_file(),
            status_code=200,
            headers={
                "Accept-Ranges": "bytes",
                "Content-Length": str(file_size),
                "Content-Type": "video/mp4",
                # Allow cross-origin canvas operations (video.crossOrigin = 'anonymous')
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Access-Control-Allow-Headers": "*",
            },
        )

    try:
        units, range_val = range_header.strip().split("=", 1)
        if units.lower() != "bytes":
            return Response(
                status_code=416,
                headers={"Content-Range": f"bytes */{file_size}"},
            )

        parts = range_val.split("-", 1)
        start_str, end_str = parts[0].strip(), parts[1].strip()

        if start_str and end_str:
            start = int(start_str)
            end = int(end_str)
        elif start_str:
            start = int(start_str)
            end = file_size - 1
        elif end_str:
            start = max(0, file_size - int(end_str))
            end = file_size - 1
        else:
            return Response(
                status_code=416,
                headers={"Content-Range": f"bytes */{file_size}"},
            )

        if start >= file_size or start < 0 or end >= file_size or start > end:
            return Response(
                status_code=416,
                headers={"Content-Range": f"bytes */{file_size}"},
            )

    except Exception:
        return Response(
            status_code=416,
            headers={"Content-Range": f"bytes */{file_size}"},
        )

    content_length = end - start + 1

    def iter_range(offset: int, length: int):
        with open(file_path, "rb") as f:
            f.seek(offset)
            bytes_left = length
            while bytes_left > 0:
                read_bytes = min(bytes_left, CHUNK_SIZE)
                data = f.read(read_bytes)
                if not data:
                    break
                bytes_left -= len(data)
                yield data

    headers = {
        "Content-Range": f"bytes {start}-{end}/{file_size}",
        "Accept-Ranges": "bytes",
        "Content-Length": str(content_length),
        "Content-Type": "video/mp4",
        # Allow cross-origin canvas operations (video.crossOrigin = 'anonymous')
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, OPTIONS",
        "Access-Control-Allow-Headers": "*",
    }

    return StreamingResponse(
        iter_range(start, content_length),
        status_code=206,
        headers=headers,
    )
