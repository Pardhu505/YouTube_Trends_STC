import os
import requests
from datetime import datetime, timedelta
from typing import List, Optional
from ..models.video import VideoResponse, VideoSearchRequest
import logging

logger = logging.getLogger(__name__)

class YouTubeService:
    def __init__(self):
        self.api_key = os.environ.get('YOUTUBE_API_KEY', 'AIzaSyARJuopfYemFZcnx9E9vR5rt8QOPl23Dto')
        self.base_url = "https://www.googleapis.com/youtube/v3"
        
    def search_videos(self, search_request: VideoSearchRequest) -> List[VideoResponse]:
        """
        Search for trending YouTube videos based on keywords and date range
        """
        try:
            # Get video search results
            search_results = self._search_videos_api(search_request)
            
            # Get detailed video statistics
            video_ids = [video['id']['videoId'] for video in search_results if video['id']['kind'] == 'youtube#video']
            
            if not video_ids:
                return []
            
            # Get video details including statistics
            detailed_videos = self._get_video_details(video_ids)
            
            # Convert to VideoResponse objects
            videos = []
            for video in detailed_videos:
                video_response = self._convert_to_video_response(video)
                if video_response:
                    videos.append(video_response)
            
            return videos
            
        except Exception as e:
            logger.error(f"Error searching videos: {str(e)}")
            return []
    
    def _search_videos_api(self, search_request: VideoSearchRequest) -> List[dict]:
        """
        Search YouTube API for videos
        """
        url = f"{self.base_url}/search"
        
        # Convert date strings to RFC 3339 format
        published_after = f"{search_request.startDate}T00:00:00Z"
        published_before = f"{search_request.endDate}T23:59:59Z"
        
        params = {
            'key': self.api_key,
            'part': 'snippet',
            'q': search_request.keywords,
            'type': 'video',
            'regionCode': search_request.region,
            'publishedAfter': published_after,
            'publishedBefore': published_before,
            'order': 'viewCount',
            'maxResults': 50,
            'relevanceLanguage': 'te' if search_request.region == 'IN' else 'en'
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        return response.json().get('items', [])
    
    def _get_video_details(self, video_ids: List[str]) -> List[dict]:
        """
        Get detailed information about videos including statistics
        """
        url = f"{self.base_url}/videos"
        
        params = {
            'key': self.api_key,
            'part': 'snippet,statistics',
            'id': ','.join(video_ids)
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        return response.json().get('items', [])
    
    def _convert_to_video_response(self, video: dict) -> Optional[VideoResponse]:
        """
        Convert YouTube API response to VideoResponse object
        """
        try:
            snippet = video['snippet']
            statistics = video['statistics']
            
            # Get the best thumbnail available
            thumbnails = snippet.get('thumbnails', {})
            thumbnail_url = (
                thumbnails.get('maxres', {}).get('url') or
                thumbnails.get('standard', {}).get('url') or
                thumbnails.get('high', {}).get('url') or
                thumbnails.get('medium', {}).get('url') or
                thumbnails.get('default', {}).get('url') or
                ''
            )
            
            # Parse published date
            published_at = datetime.fromisoformat(snippet['publishedAt'].replace('Z', '+00:00'))
            
            # Get statistics with default values
            views = int(statistics.get('viewCount', 0))
            likes = int(statistics.get('likeCount', 0))
            comments = int(statistics.get('commentCount', 0))
            
            # Analyze sentiment based on title and description
            sentiment = self._analyze_sentiment(snippet['title'], snippet.get('description', ''))
            
            return VideoResponse(
                id=video['id'],
                title=snippet['title'],
                channel=snippet['channelTitle'],
                description=snippet.get('description', '')[:200] + '...' if len(snippet.get('description', '')) > 200 else snippet.get('description', ''),
                thumbnail=thumbnail_url,
                url=f"https://www.youtube.com/watch?v={video['id']}",
                views=views,
                likes=likes,
                comments=comments,
                timestamp=published_at,
                sentiment=sentiment,
                source="YouTube"
            )
            
        except Exception as e:
            logger.error(f"Error converting video: {str(e)}")
            return None
    
    def _analyze_sentiment(self, title: str, description: str) -> str:
        """
        Rule-based sentiment analysis for Telugu/Indian content
        """
        text = f"{title} {description}".lower()
        
        # Positive keywords
        positive_keywords = [
            'best', 'amazing', 'great', 'excellent', 'wonderful', 'fantastic',
            'success', 'hit', 'blockbuster', 'record', 'celebration', 'festival',
            'victory', 'win', 'achievement', 'proud', 'happy', 'joy',
            'super', 'mass', 'power', 'energy', 'love', 'beautiful',
            'stunning', 'incredible', 'outstanding', 'brilliant'
        ]
        
        # Negative keywords
        negative_keywords = [
            'worst', 'bad', 'terrible', 'awful', 'disaster', 'flop',
            'failure', 'disappointed', 'sad', 'angry', 'hate', 'boring',
            'waste', 'problem', 'issue', 'controversy', 'scandal',
            'accident', 'death', 'violence', 'crime', 'fraud',
            'corrupt', 'poor', 'struggle', 'difficult', 'crisis'
        ]
        
        positive_count = sum(1 for keyword in positive_keywords if keyword in text)
        negative_count = sum(1 for keyword in negative_keywords if keyword in text)
        
        if positive_count > negative_count:
            return "Positive"
        elif negative_count > positive_count:
            return "Negative"
        else:
            return "Neutral"
    
    def get_trending_videos(self, region: str = "IN", category_id: str = "0") -> List[VideoResponse]:
        """
        Get trending videos for a specific region
        """
        try:
            url = f"{self.base_url}/videos"
            
            params = {
                'key': self.api_key,
                'part': 'snippet,statistics',
                'chart': 'mostPopular',
                'regionCode': region,
                'categoryId': category_id,
                'maxResults': 50
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            videos = response.json().get('items', [])
            
            # Convert to VideoResponse objects
            video_responses = []
            for video in videos:
                video_response = self._convert_to_video_response(video)
                if video_response:
                    video_responses.append(video_response)
            
            return video_responses
            
        except Exception as e:
            logger.error(f"Error getting trending videos: {str(e)}")
            return []