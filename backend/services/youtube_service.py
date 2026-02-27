import os
import requests
from datetime import datetime
from typing import List, Optional, Tuple
from models.video import VideoResponse, VideoSearchRequest
import logging
from google.auth.exceptions import DefaultCredentialsError

logger = logging.getLogger(__name__)

class YouTubeService:
    def __init__(self):
        self.api_key = os.environ.get('YOUTUBE_API_KEY', 'AIzaSyByIcDjLKKMIp3-6xplEyHtNN8EchI-kq4')
        self.base_url = "https://www.googleapis.com/youtube/v3"
        try:
            from google.cloud import translate_v2 as translate
            from google.cloud import language_v1
            self.translate_client = translate.Client()
            self.language_client = language_v1.LanguageServiceClient()
            self.google_cloud_available = True
        except (ImportError, DefaultCredentialsError):
            self.translate_client = None
            self.language_client = None
            self.google_cloud_available = False

    def search_videos(self, search_request: VideoSearchRequest) -> Tuple[List[VideoResponse], int]:
        """
        Search for trending YouTube videos based on keywords and date range
        """
        # Get video search results
        search_results, total_results = self._search_videos_api(search_request)

        # Get detailed video statistics
        video_ids = [video['id']['videoId'] for video in search_results if video['id']['kind'] == 'youtube#video']

        if not video_ids:
            return [], 0

        # Get video details including statistics
        detailed_videos = self._get_video_details(video_ids)

        # Convert to VideoResponse objects
        videos = []
        for video in detailed_videos:
            video_response = self._convert_to_video_response(video, search_request.keywords)
            if video_response:
                videos.append(video_response)

        return videos, total_results

    def _search_videos_api(self, search_request: VideoSearchRequest) -> Tuple[List[dict], int]:
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
            'maxResults': search_request.page_size,
            'relevanceLanguage': 'te' if search_request.region == 'IN' else 'en'
        }

        next_page_token = None

        # Loop through pages to get to the desired one
        for i in range(search_request.page):
            if next_page_token:
                params['pageToken'] = next_page_token

            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            # If this is the last page in the loop, return its data
            if i == search_request.page - 1:
                videos = data.get('items', [])
                total_results = data.get('pageInfo', {}).get('totalResults', 0)
                return videos, total_results

            next_page_token = data.get('nextPageToken')

            # If there's no next page, we can't continue.
            if not next_page_token:
                total_results = data.get('pageInfo', {}).get('totalResults', 0)
                return [], total_results

        # Should not be reached if search_request.page >= 1
        return [], 0

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

    def _convert_to_video_response(self, video: dict, keywords: str) -> Optional[VideoResponse]:
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
            sentiment = self._analyze_sentiment(snippet['title'], snippet.get('description', ''), keywords)

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

    def _translate_text(self, text: str, target_language: str = 'en') -> str:
        """Translates text into the target language."""
        if not self.google_cloud_available:
            return text
        result = self.translate_client.translate(text, target_language=target_language)
        return result['translatedText']

    def _analyze_sentiment(self, title: str, description: str, keywords: str) -> str:
        """
        Analyzes the sentiment of the provided text in the context of the search keywords.
        """
        text = f"{title} {description}"
        search_keywords = keywords.lower().split()

        if self.google_cloud_available:
            try:
                from google.cloud import language_v1
                # Detect language
                try:
                    detection = self.translate_client.detect_language(text)
                    language = detection['language']
                except Exception as e:
                    logger.error(f"Language detection failed: {e}")
                    language = 'en' # Default to English

                # Translate if necessary
                if language == 'te':
                    try:
                        text = self._translate_text(text)
                    except Exception as e:
                        logger.error(f"Translation failed: {e}")


                document = language_v1.Document(content=text, type_=language_v1.Document.Type.PLAIN_TEXT)

                sentiment = self.language_client.analyze_sentiment(document=document).document_sentiment

                # Context-aware sentiment
                for keyword in search_keywords:
                    if keyword in text.lower():
                        if sentiment.score > 0.25:
                            return "Positive"
                        elif sentiment.score < -0.25:
                            return "Negative"
                return "Neutral"

            except Exception as e:
                logger.error(f"Sentiment analysis failed: {e}")
        
        # Fallback to keyword-based sentiment analysis
        text = text.lower()
        positive_keywords = [
            'best', 'amazing', 'great', 'excellent', 'wonderful', 'fantastic',
            'success', 'hit', 'blockbuster', 'record', 'celebration', 'festival',
            'victory', 'win', 'achievement', 'proud', 'happy', 'joy',
            'super', 'mass', 'power', 'energy', 'love', 'beautiful',
            'stunning', 'incredible', 'outstanding', 'brilliant'
        ]

        negative_keywords = [
            'worst', 'bad', 'terrible', 'awful', 'disaster', 'flop',
            'failure', 'disappointed', 'sad', 'angry', 'hate', 'boring',
            'waste', 'problem', 'issue', 'controversy', 'scandal',
            'accident', 'death', 'violence', 'crime', 'fraud',
            'corrupt', 'poor', 'struggle', 'difficult', 'crisis'
        ]

        positive_count = 0
        negative_count = 0

        for keyword in search_keywords:
            if keyword in text:
                positive_count += sum(1 for pk in positive_keywords if pk in text)
                negative_count += sum(1 for nk in negative_keywords if nk in text)

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
                video_response = self._convert_to_video_response(video, "")
                if video_response:
                    video_responses.append(video_response)
            
            return video_responses
            
        except Exception as e:
            logger.error(f"Error getting trending videos: {str(e)}")
            return []
