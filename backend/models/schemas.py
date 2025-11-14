"""
Pydantic models for request/response validation
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from enum import Enum

class FileMetadata(BaseModel):
    """Metadata for uploaded file"""
    filename: str
    size: int
    path: str
    tokens: Optional[int] = None
    functions: List[str] = []
    classes: List[str] = []

class UploadResponse(BaseModel):
    """Response after file upload"""
    session_id: str
    files_uploaded: int
    total_size: int
    total_tokens: int
    files: List[FileMetadata]

class TaskStatus(str, Enum):
    """Status of documentation generation task"""
    PENDING = "pending"
    PROCESSING = "processing"
    ANALYZING = "analyzing"
    DOCUMENTING = "documenting"
    COMPLETED = "completed"
    FAILED = "failed"

class GenerationRequest(BaseModel):
    """Request to generate documentation"""
    session_id: str
    project_name: Optional[str] = "Project"
    include_examples: bool = True

class GenerationStatus(BaseModel):
    """Status of generation process"""
    session_id: str
    status: TaskStatus
    progress: int = Field(ge=0, le=100)
    current_stage: str
    message: str
    files_processed: int
    total_files: int
    estimated_time_remaining: Optional[int] = None  # seconds

class GenerationResult(BaseModel):
    """Final result of documentation generation"""
    session_id: str
    status: TaskStatus
    files_generated: List[str]
    download_urls: List[str]
    metadata: Dict
