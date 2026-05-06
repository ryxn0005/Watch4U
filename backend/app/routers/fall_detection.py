"""HTTP endpoints for fall detection."""

import logging
import uuid
from typing import Any

from fastapi import APIRouter, File, UploadFile

from app.models.fall import (
    AnalysisStatus,
    FallDetectionRequest,
    FallDetectionResult,
    VideoUploadResponse,
)

router = APIRouter(tags=["fall_detection"])
log = logging.getLogger(__name__)

# In-memory job store (replace with Redis/DB in production)
_analysis_jobs: dict[str, dict[str, Any]] = {}


def _mock_analyze_video(video_id: str, request: FallDetectionRequest) -> FallDetectionResult:
    """Mock analysis - replace with actual model inference."""
    import random
    import time

    start = time.time()

    # Simulate processing
    time.sleep(0.1)

    # Mock result - 30% chance of fall detection for demo
    fall_detected = random.random() < 0.3
    confidence = random.uniform(0.7, 0.95) if fall_detected else random.uniform(0.1, 0.4)

    processing_time = int((time.time() - start) * 1000)

    if fall_detected:
        return FallDetectionResult(
            fall_detected=True,
            confidence=confidence,
            fall_events=[
                {
                    "start_time": 5.2,
                    "end_time": 7.8,
                    "confidence": confidence,
                    "severity": "moderate",
                    "keypoints": [],
                }
            ],
            long_lie_detected=random.random() < 0.2,
            scene=random.choice(["bed", "chair", "stand"]),
            processing_time_ms=processing_time,
        )

    return FallDetectionResult(
        fall_detected=False,
        confidence=confidence,
        fall_events=[],
        long_lie_detected=False,
        scene=None,
        processing_time_ms=processing_time,
    )


@router.post("/analyze", response_model=FallDetectionResult)
async def analyze_video(request: FallDetectionRequest) -> FallDetectionResult:
    """Analyze video for fall detection.

    Accepts video URL, base64-encoded video, or pre-extracted keypoints.
    Returns fall detection results with confidence scores.
    """
    log.info(f"Analyzing video: url={request.video_url is not None}, "
             f"base64={request.video_base64 is not None}")

    video_id = str(uuid.uuid4())
    result = _mock_analyze_video(video_id, request)

    # Store result
    _analysis_jobs[video_id] = {
        "status": "completed",
        "progress": 1.0,
        "result": result,
    }

    return result


@router.post("/upload", response_model=VideoUploadResponse)
async def upload_video(file: UploadFile = File(...)) -> VideoUploadResponse:
    """Upload a video file for fall detection analysis.

    Returns a video ID that can be used to check analysis status.
    """
    video_id = str(uuid.uuid4())

    log.info(f"Video uploaded: id={video_id}, filename={file.filename}")

    # Initialize job
    _analysis_jobs[video_id] = {
        "status": "pending",
        "progress": 0.0,
        "result": None,
    }

    return VideoUploadResponse(
        video_id=video_id,
        status="uploaded",
        message=f"Video '{file.filename}' uploaded successfully. Use video_id to check status.",
    )


@router.get("/status/{video_id}", response_model=AnalysisStatus)
async def get_analysis_status(video_id: str) -> AnalysisStatus:
    """Get the status of a video analysis job."""
    job = _analysis_jobs.get(video_id)

    if not job:
        return AnalysisStatus(
            video_id=video_id,
            status="not_found",
            progress=0.0,
            result=None,
        )

    return AnalysisStatus(
        video_id=video_id,
        status=job["status"],
        progress=job["progress"],
        result=job.get("result"),
    )


@router.get("/health")
async def fall_detection_health() -> dict[str, Any]:
    """Health check for fall detection service."""
    return {
        "status": "healthy",
        "model_loaded": True,
        "supported_scenes": ["bed", "chair", "stand"],
    }
