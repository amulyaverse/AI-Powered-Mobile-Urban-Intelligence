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
POTHOLE_VIDEOS_DIR = PROJECT_ROOT / "edge-ai" / "Pothole_Road_Condition_Model"
CHUNK_SIZE = 1024 * 512  # 512 KB

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
def stream_sample_video(filename: str, request: Request):
    """
    Stream a sample MP4 video with HTTP 206 Partial Content Range request support for seeking.
    """
    safe_filename = Path(filename).name
    file_path = POTHOLE_VIDEOS_DIR / safe_filename

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
    }

    return StreamingResponse(
        iter_range(start, content_length),
        status_code=206,
        headers=headers,
    )
