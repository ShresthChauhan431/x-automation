from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Literal
from datetime import datetime
import uuid

# --- Enums ---
class SignalType(BaseModel):
    source: Literal["TIMELINE", "KEYWORD", "LIST", "REPLY"]

class ContentType(BaseModel):
    type: Literal["TWEET", "THREAD", "REPLY"]

# --- Core Domain Models ---

class Signal(BaseModel):
    """Raw input observed from the world."""
    id: str
    content: str
    author_id: str
    created_at: datetime
    url: Optional[str] = None
    metadata: Dict = Field(default_factory=dict)
    
    # Computed Scores
    novelty_score: float = 0.0
    authority_score: float = 0.0
    urgency_score: float = 0.0

class ResearchOutput(BaseModel):
    """Output from the Research & RAG module."""
    source_signal_id: str
    core_claim: str
    implications: List[str]
    attack_vectors: List[str]
    raw_source_summary: str

class Insight(BaseModel):
    """Compressed wisdom ready for storage."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    original_research_id: Optional[str]
    content: str
    embedding: Optional[List[float]] = None
    created_at: datetime = Field(default_factory=datetime.now)
    fitness_score: float = 0.5

class Hook(BaseModel):
    """A template or pattern for generating content."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    template_text: str
    structure_type: str  # e.g., "Contrarian", "Prediction", "Question"
    emotional_polarity: str # "Positive", "Negative", "Neutral"
    historical_performance: float = 0.0
    saturation_score: float = 0.0

class TweetContent(BaseModel):
    """Ready-to-post content."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    text: str
    thread_children: List[str] = Field(default_factory=list)
    hook_id: Optional[str]
    insight_id: Optional[str]
    status: Literal["DRAFT", "PENDING_APPROVAL", "POSTED", "REJECTED"] = "DRAFT"
    created_at: datetime = Field(default_factory=datetime.now)
    scheduled_time: Optional[datetime] = None
