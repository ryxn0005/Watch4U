"""Pydantic models for fall detection."""

from typing import Any

from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    """Bounding box for detected person."""
    x: float
    y: float
    width: float
    height: float
    confidence: float


class Keypoint(BaseModel):
    """Body keypoint from pose estimation."""
    name: str
    x: float
    y: float
    confidence: float


class FallDetectionRequest(BaseModel):
    """Request for fall detection analysis."""
    video_url: str | None = Field(default=None, description="URL to video file")
    video_base64: str | None = Field(default=None, description="Base64-encoded video")
    frame_data: list[dict[str, Any]] | None = Field(
        default=None, description="Pre-extracted frame keypoints"
    )
    sample_rate: int = Field(default=5, ge=1, description="Frames per second to analyze")


class FallEvent(BaseModel):
    """Detected fall event."""
    start_time: float = Field(..., description="Event start time in seconds")
    end_time: float = Field(..., description="Event end time in seconds")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence")
    severity: str = Field(default="unknown", description="Fall severity: minor, moderate, severe")
    keypoints: list[Keypoint] = Field(default_factory=list)


class FallDetectionResult(BaseModel):
    """Result of fall detection analysis."""
    fall_detected: bool
    confidence: float = Field(..., ge=0.0, le=1.0)
    fall_events: list[FallEvent] = Field(default_factory=list)
    long_lie_detected: bool = Field(default=False, description="Person remained down > 60s")
    scene: str | None = Field(default=None, description="Detected scene: bed, chair, stand")
    processing_time_ms: int


class VideoUploadResponse(BaseModel):
    """Response after video upload."""
    video_id: str
    status: str
    message: str


class AnalysisStatus(BaseModel):
    """Status of video analysis job."""
    video_id: str
    status: str = Field(..., description="pending, processing, completed, failed")
    progress: float = Field(..., ge=0.0, le=1.0)
    result: FallDetectionResult | None = None
