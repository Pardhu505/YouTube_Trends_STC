from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import uuid

class VideoSearchRequest(BaseModel):
    keywords: str
    startDate: str
    endDate: str
    region: str = "IN"
    page: int = 1
    page_size: int = 10

class VideoResponse(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    channel: str
    description: str
    thumbnail: str
    url: str
    views: int
    likes: int
    comments: int
    timestamp: datetime
    sentiment: str
    source: str = "YouTube"

class SearchResponse(BaseModel):
    videos: List[VideoResponse]
    total_count: int
    search_params: VideoSearchRequest