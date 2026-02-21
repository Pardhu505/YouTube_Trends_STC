import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor for logging
apiClient.interceptors.request.use(
  (config) => {
    console.log('API Request:', config.method?.toUpperCase(), config.url);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Add response interceptor for error handling

apiClient.interceptors.response.use(
  (response) => {
    console.log('API Response:', response.status, response.config.url);
    return response;
  },
  (error) => {
    // FIX: Only log as a hard error if it is NOT a 404
    if (error.response?.status !== 404) {
      console.error('API Response Error:', error);
      if (error.response) {
        console.error('Error Data:', error.response.data);
        console.error('Error Status:', error.response.status);
      }
    }
    return Promise.reject(error);
  }
);;

export const youtubeAPI = {
  // Search for YouTube videos
  searchVideos: async (searchParams) => {
    try {
      const response = await apiClient.post('/youtube/search', searchParams);
      return response.data;
    } catch (error) {
      console.error('Error searching videos:', error);
      throw error;
    }
  },

  // Get trending videos
  getTrendingVideos: async (region = 'IN', categoryId = '0') => {
    try {
      const response = await apiClient.get(`/youtube/trending?region=${region}&category_id=${categoryId}`);
      return response.data;
    } catch (error) {
      console.error('Error getting trending videos:', error);
      throw error;
    }
  },

  // Export to CSV
  exportCSV: async (searchParams) => {
    try {
      const response = await apiClient.post('/export/csv', searchParams, {
        responseType: 'blob',
        headers: {
          'Accept': 'text/csv'
        }
      });
      
      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'youtube_trends_report.csv');
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      return true;
    } catch (error) {
      console.error('Error exporting CSV:', error);
      throw error;
    }
  },

  // Export to PDF
  exportPDF: async (searchParams) => {
    try {
      const response = await apiClient.post('/export/pdf', searchParams, {
        responseType: 'blob',
        headers: {
          'Accept': 'application/pdf'
        }
      });
      
      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'youtube_trends_report.pdf');
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      return true;
    } catch (error) {
      console.error('Error exporting PDF:', error);
      throw error;
    }
  },

  // Get analytics summary
  getAnalyticsSummary: async (searchParams) => {
    try {
      const response = await apiClient.post('/youtube/analytics', searchParams);
      return response.data;
    } catch (error) {
      // FIX: If 404, return empty data instead of throwing an error to the UI
      if (error.response && error.response.status === 404) {
        return {
          total_videos: 0,
          sentiment_distribution: { positive: 0, negative: 0, neutral: 0 },
          overall_sentiment: "Neutral",
          total_views: 0,
          total_likes: 0,
          total_comments: 0,
          total_engagement: 0
        };
      }
      
      console.error('Error getting analytics summary:', error);
      throw error;
    }
  }

export default apiClient;
