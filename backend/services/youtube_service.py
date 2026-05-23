import os
import requests
from datetime import datetime
from typing import List, Optional, Tuple
from models.video import VideoResponse, VideoSearchRequest
import logging
from google.auth.exceptions import DefaultCredentialsError

logger = logging.getLogger(__name__)

class YouTubeAPIError(Exception):
    """Base exception for YouTube API errors"""
    def __init__(self, message, status_code=None, reason=None):
        self.message = message
        self.status_code = status_code
        self.reason = reason
        super().__init__(self.message)

class YouTubeQuotaExceeded(YouTubeAPIError):
    """Exception raised when YouTube API quota is exceeded"""
    pass

class YouTubeServiceBlocked(YouTubeAPIError):
    """Exception raised when the YouTube API service is blocked for the key"""
    pass

class YouTubeService:
    def __init__(self):
        self.api_keys = []
        env_keys = os.environ.get('YOUTUBE_API_KEYS') or os.environ.get('YOUTUBE_API_KEY')
        if env_keys:
            self.api_keys.extend([k.strip() for k in env_keys.split(',') if k.strip()])

        if not self.api_keys:
            logger.warning("No YouTube API keys found in environment variables.")
        self.current_key_index = 0
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
                # Apply sentiment filter if provided
                sentiment_filter = getattr(search_request, 'sentiment', None)
                if sentiment_filter and sentiment_filter != 'All':
                    if video_response.sentiment.lower() == sentiment_filter.lower():
                        videos.append(video_response)
                else:
                    videos.append(video_response)

        # If filtered, update total count
        sentiment_filter = getattr(search_request, 'sentiment', None)
        if sentiment_filter and sentiment_filter != 'All':
            total_results = len(videos)

        return videos, total_results

    def _get_current_key(self) -> str:
        """Returns the current API key based on the index."""
        if not self.api_keys:
            return ""
        # Ensure index wraps around or stays within bounds
        self.current_key_index = self.current_key_index % len(self.api_keys)
        return self.api_keys[self.current_key_index]

    def _execute_with_key_rotation(self, request_func, *args, **kwargs):
        """
        Executes a request function and rotates the API key if a quota/auth error occurs.
        The request_func must accept 'api_key' as a keyword argument.
        """
        attempts = 0
        max_attempts = len(self.api_keys) if self.api_keys else 1
        last_error_details = None

        while attempts < max_attempts:
            current_key = self._get_current_key()
            try:
                kwargs['api_key'] = current_key
                return request_func(*args, **kwargs)
            except requests.exceptions.HTTPError as e:
                status_code = e.response.status_code if getattr(e, 'response', None) is not None else None

                # Parse error response for better diagnostics
                error_msg = str(e)
                reason = None
                try:
                    error_data = e.response.json().get('error', {})
                    error_msg = error_data.get('message', str(e))
                    reason = error_data.get('errors', [{}])[0].get('reason', None)
                except Exception:
                    pass

                last_error_details = {
                    'status_code': status_code,
                    'message': error_msg,
                    'reason': reason
                }

                # 403 (Quota exceeded or blocked) or 400 (Invalid key)
                if status_code in [403, 400]:
                    logger.warning(f"YouTube API Error {status_code} ({reason}) with key {current_key[:10]}... Switching to next key. Error: {error_msg}")
                    self.current_key_index += 1
                    attempts += 1
                    if attempts >= max_attempts:
                        logger.error(f"All available YouTube API keys have failed. Last error: {error_msg}")

                        if reason == 'quotaExceeded':
                            raise YouTubeQuotaExceeded(f"YouTube API quota exceeded: {error_msg}", status_code=status_code, reason=reason)
                        elif reason == 'forbidden' or 'blocked' in error_msg.lower():
                            raise YouTubeServiceBlocked(f"YouTube API key blocked or access forbidden: {error_msg}", status_code=status_code, reason=reason)
                        else:
                            raise YouTubeAPIError(f"YouTube API Error: {error_msg}", status_code=status_code, reason=reason)
                else:
                    # Other HTTP errors (e.g., 500) are raised immediately
                    raise e

        raise YouTubeAPIError("Failed to execute request after exhausting API keys.")

    def _search_videos_api(self, search_request: VideoSearchRequest) -> Tuple[List[dict], int]:
        """
        Search YouTube API for videos
        """
        def _make_search_request(api_key):
            url = f"{self.base_url}/search"

            # Convert date strings to RFC 3339 format
            published_after = f"{search_request.startDate}T00:00:00Z"
            published_before = f"{search_request.endDate}T23:59:59Z"

            params = {
                'key': api_key,
                'part': 'snippet',
                'q': search_request.keywords,
                'type': 'video',
                'regionCode': search_request.region,
                'publishedAfter': published_after,
                'publishedBefore': published_before,
                'order': 'viewCount',
                'maxResults': min(search_request.page_size, 50),
                'relevanceLanguage': 'te' if search_request.region == 'IN' else 'en'
            }

            all_videos = []
            next_page_token = None

            # If we need more than 50 results (the API limit per request),
            # we need to iterate through pages.
            # But the current architecture uses 'page' for pagination in the UI.
            # So if UI asks for page 1 with page_size 200, we should return 200 results.

            target_results_count = search_request.page_size
            pages_to_fetch = (target_results_count + 49) // 50 # 1 if <= 50, 2 if <= 100, etc.

            # First, skip to the requested "page"
            # Each "page" in the UI is considered a set of 'page_size' results.
            # So if page=2 and page_size=200, we skip 200 results first.
            results_to_skip = (search_request.page - 1) * search_request.page_size

            while results_to_skip > 0:
                skip_params = params.copy()
                skip_params['maxResults'] = min(results_to_skip, 50)
                if next_page_token:
                    skip_params['pageToken'] = next_page_token

                response = requests.get(url, params=skip_params)
                response.raise_for_status()
                data = response.json()

                next_page_token = data.get('nextPageToken')
                if not next_page_token:
                    return [], data.get('pageInfo', {}).get('totalResults', 0)

                results_to_skip -= skip_params['maxResults']

            # Now fetch the actual results
            total_results = 0
            while len(all_videos) < target_results_count:
                fetch_params = params.copy()
                fetch_params['maxResults'] = min(target_results_count - len(all_videos), 50)
                if next_page_token:
                    fetch_params['pageToken'] = next_page_token

                response = requests.get(url, params=fetch_params)
                response.raise_for_status()
                data = response.json()

                all_videos.extend(data.get('items', []))
                total_results = data.get('pageInfo', {}).get('totalResults', 0)

                next_page_token = data.get('nextPageToken')
                if not next_page_token:
                    break

            return all_videos, total_results

        return self._execute_with_key_rotation(_make_search_request)

    def _get_video_details(self, video_ids: List[str]) -> List[dict]:
        """
        Get detailed information about videos including statistics.
        Batches requests in chunks of 50 to comply with YouTube API limits.
        """
        all_details = []
        # YouTube API allows maximum 50 IDs per request
        chunk_size = 50

        for i in range(0, len(video_ids), chunk_size):
            chunk = video_ids[i:i + chunk_size]

            def _make_details_request(api_key, chunk_ids=chunk):
                url = f"{self.base_url}/videos"
                params = {
                    'key': api_key,
                    'part': 'snippet,statistics',
                    'id': ','.join(chunk_ids)
                }
                response = requests.get(url, params=params)
                response.raise_for_status()
                return response.json().get('items', [])

            details_chunk = self._execute_with_key_rotation(_make_details_request)
            all_details.extend(details_chunk)

        return all_details

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
        def _make_trending_request(api_key):
            url = f"{self.base_url}/videos"
            
            params = {
                'key': api_key,
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
            
        try:
            return self._execute_with_key_rotation(_make_trending_request)
        except Exception as e:
            logger.error(f"Error getting trending videos: {str(e)}")
            return []
