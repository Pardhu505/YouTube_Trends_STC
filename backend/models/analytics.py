from pydantic import BaseModel
from typing import Dict, List

class SentimentDistribution(BaseModel):
    positive: int
    negative: int
    neutral: int

class AnalyticsSummary(BaseModel):
    total_videos: int
    sentiment_distribution: SentimentDistribution
    overall_sentiment: str
    average_engagement: Dict[str, float]
    total_views: int
    total_likes: int
    total_comments: int
    total_engagement: int
