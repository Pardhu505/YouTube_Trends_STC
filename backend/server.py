import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse, Response
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List
import uuid
from datetime import datetime
import io
import asyncio
import requests

# Import our services and models
from models.video import VideoSearchRequest, VideoResponse, SearchResponse
from models.analytics import AnalyticsSummary, SentimentDistribution
from services.youtube_service import YouTubeService
from services.export_service import ExportService

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection with better error handling
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/youtube_trends')
db_name = os.environ.get('DB_NAME', 'youtube_trends')

try:
    client = AsyncIOMotorClient(mongo_url, serverSelectionTimeoutMS=5000)
    db = client[db_name]
    print(f"Connected to MongoDB: {db_name}")
except Exception as e:
    print(f"MongoDB connection error: {e}")
    client = None
    db = None

# Create the main app without a prefix
app = FastAPI(
    title="YouTube Trends Analytics API",
    description="API for analyzing YouTube trends and generating reports",
    version="1.0.0"
)

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Initialize services
youtube_service = YouTubeService()
export_service = ExportService()

# Define Models
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

# Health check endpoint
@api_router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "database": "connected" if db is not None else "disconnected"
    }

# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "YouTube Trends Analytics API is running"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    if db is not None:
        _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    if db is None:
        return []
    try:
        status_checks = await db.status_checks.find().to_list(1000)
        return [StatusCheck(**status_check) for status_check in status_checks]
    except:
        return []

@api_router.post("/youtube/search", response_model=SearchResponse)
async def search_youtube_videos(search_request: VideoSearchRequest):
    """
    Search for YouTube videos based on keywords, date range, and region
    """
    try:
        # Search for videos using YouTube API with timeout
        videos, total_count = youtube_service.search_videos(search_request)
        
        # Store search results in database (optional if DB fails)
        if db is not None:
            try:
                search_result = {
                    "search_params": search_request.dict(),
                    "videos": [video.dict() for video in videos],
                    "total_count": total_count,
                    "timestamp": datetime.utcnow()
                }
                await db.search_results.insert_one(search_result)
            except Exception as db_error:
                print(f"Database storage error: {db_error}")
        
        return SearchResponse(
            videos=videos,
            total_count=total_count,
            search_params=search_request
        )
        
    except requests.exceptions.HTTPError as e:
        logging.error(f"YouTube API Error: {str(e)}")
        if e.response.status_code == 403:
             raise HTTPException(status_code=403, detail="YouTube API quota exceeded or key invalid")
        elif e.response.status_code == 400:
             raise HTTPException(status_code=400, detail="Invalid request to YouTube API (possibly expired key)")
        elif e.response.status_code == 429:
             raise HTTPException(status_code=429, detail="Too many requests to YouTube API")
        else:
             raise HTTPException(status_code=e.response.status_code, detail=f"YouTube API Error: {str(e)}")
    except Exception as e:
        logging.error(f"Error searching videos: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error searching videos: {str(e)}")

@api_router.get("/youtube/trending")
async def get_trending_videos(region: str = "IN", category_id: str = "0"):
    """
    Get trending YouTube videos for a specific region
    """
    try:
        videos = youtube_service.get_trending_videos(region, category_id)
        
        # Store trending results in database (optional if DB fails)
        if db is not None:
            try:
                trending_result = {
                    "region": region,
                    "category_id": category_id,
                    "videos": [video.dict() for video in videos],
                    "total_count": len(videos),
                    "timestamp": datetime.utcnow()
                }
                await db.trending_results.insert_one(trending_result)
            except Exception as db_error:
                print(f"Database storage error: {db_error}")
        
        return {
            "videos": videos,
            "total_count": len(videos),
            "region": region,
            "category_id": category_id
        }
        
    except Exception as e:
        logging.error(f"Error getting trending videos: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting trending videos: {str(e)}")

@api_router.post("/export/csv")
async def export_csv(search_request: VideoSearchRequest):
    """
    Export search results to CSV format with timeout handling
    """
    try:
        # Get videos for export with shorter timeout
        videos, _ = youtube_service.search_videos(search_request)
        
        if not videos:
            raise HTTPException(status_code=404, detail="No videos found for export")
        
        # Generate CSV with memory optimization
        csv_content = export_service.export_to_csv(videos, search_request.dict())
        
        # Return as response with proper headers
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=youtube_trends_report.csv"}
        )

    except requests.exceptions.HTTPError as e:
        logging.error(f"YouTube API Error during CSV export: {str(e)}")
        if e.response.status_code == 403:
             raise HTTPException(status_code=403, detail="YouTube API quota exceeded or key invalid")
        elif e.response.status_code == 400:
             raise HTTPException(status_code=400, detail="Invalid request to YouTube API (possibly expired key)")
        elif e.response.status_code == 429:
             raise HTTPException(status_code=429, detail="Too many requests to YouTube API")
        else:
             raise HTTPException(status_code=e.response.status_code, detail=f"YouTube API Error: {str(e)}")
        
    except Exception as e:
        logging.error(f"Error exporting CSV: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error exporting CSV: {str(e)}")

@api_router.post("/export/pdf")
async def export_pdf(search_request: VideoSearchRequest):
    """
    Export search results to PDF format with timeout handling
    """
    try:
        # Get videos for export with shorter timeout
        videos, _ = youtube_service.search_videos(search_request)
        
        if not videos:
            raise HTTPException(status_code=404, detail="No videos found for export")
        
        # Limit videos for PDF to prevent memory issues
        limited_videos = videos[:20]  # Limit to 20 videos for PDF
        
        # Generate PDF with memory optimization
        pdf_content = export_service.export_to_pdf(limited_videos, search_request.dict())
        
        # Return as response with proper headers
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=youtube_trends_report.pdf"}
        )

    except requests.exceptions.HTTPError as e:
        logging.error(f"YouTube API Error during PDF export: {str(e)}")
        if e.response.status_code == 403:
             raise HTTPException(status_code=403, detail="YouTube API quota exceeded or key invalid")
        elif e.response.status_code == 400:
             raise HTTPException(status_code=400, detail="Invalid request to YouTube API (possibly expired key)")
        elif e.response.status_code == 429:
             raise HTTPException(status_code=429, detail="Too many requests to YouTube API")
        else:
             raise HTTPException(status_code=e.response.status_code, detail=f"YouTube API Error: {str(e)}")
        
    except Exception as e:
        logging.error(f"Error exporting PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error exporting PDF: {str(e)}")

@api_router.get("/analytics/summary", response_model=AnalyticsSummary)
async def get_analytics_summary():
    """
    Get a summary of all searches from the database
    """
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")

    try:
        # Check for DB connection before query
        if client:
            await client.admin.command('ismaster')
            total_searches = await db.search_results.count_documents({})
        else:
            total_searches = 0

        return AnalyticsSummary(
            total_videos=total_searches,
            sentiment_distribution=SentimentDistribution(positive=0, negative=0, neutral=0),
            overall_sentiment="Neutral",
            average_engagement={},
            total_views=0,
            total_likes=0,
            total_comments=0,
            total_engagement=0
        )
    except Exception as e:
        logging.warning(f"Analytics summary failed due to DB issue: {str(e)}")
        # Return a default summary if the database is down
        return AnalyticsSummary(
            total_videos=0,
            sentiment_distribution=SentimentDistribution(positive=0, negative=0, neutral=0),
            overall_sentiment="Neutral",
            average_engagement={},
            total_views=0,
            total_likes=0,
            total_comments=0,
            total_engagement=0
        )

@api_router.post("/youtube/analytics", response_model=AnalyticsSummary)
async def get_youtube_analytics(search_request: VideoSearchRequest):
    """
    Get analytics summary for a YouTube search
    """
    # Default empty response
    empty_response = AnalyticsSummary(
        total_videos=0,
        sentiment_distribution=SentimentDistribution(positive=0, negative=0, neutral=0),
        overall_sentiment="Neutral",
        average_engagement={"views": 0, "likes": 0, "comments": 0},
        total_views=0,
        total_likes=0,
        total_comments=0,
        total_engagement=0
    )

    try:
        videos, _ = youtube_service.search_videos(search_request)
    except Exception as e:
        logging.error(f"search_videos failed inside analytics: {str(e)}")
        return empty_response   # ← never 500, just return empty

    if not videos:
        return empty_response   # ← never 500, just return empty

    try:
        total_videos_in_search = len(videos)
        
        sentiment_distribution = {"positive": 0, "negative": 0, "neutral": 0}
        for video in videos:
            sentiment = getattr(video, 'sentiment', 'neutral')
            sentiment = sentiment.lower() if sentiment else 'neutral'
            if sentiment in sentiment_distribution:
                sentiment_distribution[sentiment] += 1
        
        overall_sentiment = max(sentiment_distribution, key=sentiment_distribution.get)

        total_views    = sum(getattr(video, 'views', 0) or 0 for video in videos)
        total_likes    = sum(getattr(video, 'likes', 0) or 0 for video in videos)
        total_comments = sum(getattr(video, 'comments', 0) or 0 for video in videos)
        
        average_engagement = {
            "views":    total_views    / total_videos_in_search,
            "likes":    total_likes    / total_videos_in_search,
            "comments": total_comments / total_videos_in_search,
        }

        return AnalyticsSummary(
            total_videos=total_videos_in_search,
            sentiment_distribution=SentimentDistribution(**sentiment_distribution),
            overall_sentiment=overall_sentiment.capitalize(),
            average_engagement=average_engagement,
            total_views=total_views,
            total_likes=total_likes,
            total_comments=total_comments,
            total_engagement=total_likes + total_comments
        )

    except Exception as e:
        logging.error(f"Error computing analytics: {str(e)}")
        return empty_response   # ← never 500, just return empty

# Include the router in the main app
app.include_router(api_router)

# Enhanced CORS for production
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],  # In production, specify your Vercel domain
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    logger.info("YouTube Trends API starting up...")

@app.on_event("shutdown")
async def shutdown_db_client():
    if client is not None:
        client.close()

# For Render deployment
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)
