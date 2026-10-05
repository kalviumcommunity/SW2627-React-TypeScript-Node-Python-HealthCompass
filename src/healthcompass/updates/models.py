"""Data models for policy updates and document versions."""

from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field


class Severity(str, Enum):
    """Severity levels for policy updates."""
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class UpdateCategory(str, Enum):
    """Categories for policy updates."""
    OUTBREAK = "outbreak"
    VACCINATION = "vaccination"
    PPE = "ppe"
    INFECTION_CONTROL = "infection_control"
    GENERAL = "general"


class UpdateStatus(str, Enum):
    """Status of policy updates."""
    PUBLISHED = "published"
    DRAFT = "draft"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"


class DocumentVersion(BaseModel):
    """A specific version of a guidance document."""
    
    id: str
    document_id: str
    version: str
    title: str
    content: str
    source_file: Optional[str] = None
    effective_date: Optional[str] = None
    published_date: Optional[str] = None
    status: str = "active"
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ChangedSection(BaseModel):
    """A specific section that changed between versions."""
    
    section_name: str
    previous_content: str
    new_content: str
    change_summary: Optional[str] = None


class PolicyUpdate(BaseModel):
    """A policy update record tracking changes between document versions."""
    
    id: str
    document_id: str
    document_title: str
    previous_version_id: str
    new_version_id: str
    previous_version: str
    new_version: str
    
    category: UpdateCategory
    severity: Severity
    status: UpdateStatus = UpdateStatus.PUBLISHED
    
    title: str
    summary: str
    
    previous_instruction: str
    new_instruction: str
    
    changed_sections: List[ChangedSection] = []
    
    effective_date: Optional[str] = None
    published_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    published_by: Optional[str] = None
    authority: Optional[str] = None
    
    # Optional fields
    change_reason: Optional[str] = None
    impact: Optional[str] = None
    region: Optional[str] = None
    
    # Read/unread tracking
    is_read: bool = False
    
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UpdateListResponse(BaseModel):
    """Response model for update list with pagination."""
    
    items: List[PolicyUpdate]
    total: int
    page: int
    page_size: int
    has_more: bool
