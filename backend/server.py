from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List
import uuid
from datetime import datetime
import io

# Import our services and models
from models.video import VideoSearchRequest, VideoResponse, SearchResponse
from services.youtube_service import YouTubeService
from services.export_service import ExportService

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

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

# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "YouTube Trends Analytics API is running"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

@api_router.post("/youtube/search", response_model=SearchResponse)
async def search_youtube_videos(search_request: VideoSearchRequest):
    """
    Search for YouTube videos based on keywords, date range, and region
    """
    try:
        # Search for videos using YouTube API
        videos = youtube_service.search_videos(search_request)
        
        # Store search results in database
        search_result = {
            "search_params": search_request.dict(),
            "videos": [video.dict() for video in videos],
            "total_count": len(videos),
            "timestamp": datetime.utcnow()
        }
        
        await db.search_results.insert_one(search_result)
        
        return SearchResponse(
            videos=videos,
            total_count=len(videos),
            search_params=search_request
        )
        
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
        
        # Store trending results in database
        trending_result = {
            "region": region,
            "category_id": category_id,
            "videos": [video.dict() for video in videos],
            "total_count": len(videos),
            "timestamp": datetime.utcnow()
        }
        
        await db.trending_results.insert_one(trending_result)
        
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
    Export search results to CSV format
    """
    try:
        # Get videos for export
        videos = youtube_service.search_videos(search_request)
        
        # Generate CSV
        csv_content = export_service.export_to_csv(videos, search_request.dict())
        
        # Create streaming response
        def iter_csv():
            yield csv_content
        
        response = StreamingResponse(
            iter_csv(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=youtube_trends_report.csv"}
        )
        
        return response
        
    except Exception as e:
        logging.error(f"Error exporting CSV: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error exporting CSV: {str(e)}")

@api_router.post("/export/pdf")
async def export_pdf(search_request: VideoSearchRequest):
    """
    Export search results to PDF format
    """
    try:
        # Get videos for export
        videos = youtube_service.search_videos(search_request)
        
        # Generate PDF
        pdf_content = export_service.export_to_pdf(videos, search_request.dict())
        
        # Create streaming response
        def iter_pdf():
            yield pdf_content
        
        response = StreamingResponse(
            io.BytesIO(pdf_content),
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=youtube_trends_report.pdf"}
        )
        
        return response
        
    except Exception as e:
        logging.error(f"Error exporting PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error exporting PDF: {str(e)}")

@api_router.get("/analytics/summary")
async def get_analytics_summary():
    """
    Get analytics summary from stored data
    """
    try:
        # Get recent search results
        recent_searches = await db.search_results.find().sort("timestamp", -1).limit(10).to_list(10)
        
        # Calculate summary statistics
        total_searches = await db.search_results.count_documents({})
        
        summary = {
            "total_searches": total_searches,
            "recent_searches": len(recent_searches),
            "last_updated": datetime.utcnow().isoformat()
        }
        
        return summary
        
    except Exception as e:
        logging.error(f"Error getting analytics summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting analytics summary: {str(e)}")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)