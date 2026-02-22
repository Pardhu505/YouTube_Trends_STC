from fastapi.testclient import TestClient
from server import app
from unittest.mock import MagicMock, patch
from models.video import VideoSearchRequest

client = TestClient(app)

def test_analytics_handles_error():
    # Mock youtube_service.search_videos to raise an exception
    with patch('server.youtube_service.search_videos') as mock_search:
        mock_search.side_effect = Exception("Some external API error")

        response = client.post("/api/youtube/analytics", json={
            "keywords": "test",
            "startDate": "2026-01-01",
            "endDate": "2026-01-31",
            "region": "IN"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["total_videos"] == 0
        assert data["overall_sentiment"] == "Neutral"

def test_analytics_handles_no_videos():
    # Mock youtube_service.search_videos to return empty list
    with patch('server.youtube_service.search_videos') as mock_search:
        mock_search.return_value = ([], 0)

        response = client.post("/api/youtube/analytics", json={
            "keywords": "test",
            "startDate": "2026-01-01",
            "endDate": "2026-01-31",
            "region": "IN"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["total_videos"] == 0
