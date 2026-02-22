import React, { useState, useEffect } from 'react';
import './App.css';
import Header from './components/Header';
import SearchForm from './components/SearchForm';
import ResultsTable from './components/ResultsTable';
import Summary from './components/Summary';
import { youtubeAPI } from './services/api';
import { useToast } from './hooks/use-toast';
import { Toaster } from './components/ui/sonner';

function App() {
  const [searchResults, setSearchResults] = useState([]);
  const [filteredSearchResults, setFilteredSearchResults] = useState([]);
  const [summaryData, setSummaryData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeSentiment, setActiveSentiment] = useState('All');
  const [hasSearched, setHasSearched] = useState(false);
  const [currentSearchParams, setCurrentSearchParams] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalResults, setTotalResults] = useState(0);
  const [pageSize, setPageSize] = useState(10);
  const { toast } = useToast();

  const handleSearch = async (searchParams, page = 1) => {
    setLoading(true);
    setCurrentPage(page);
    
    // Ensure searchParams don't contain pagination info for consistent state
    const { page: ignoredPage, ...searchOnlyParams } = searchParams;
    setCurrentSearchParams(searchOnlyParams);

    const params = { ...searchOnlyParams, page, page_size: pageSize };

    try {
      const [videoResponse, summaryResponse] = await Promise.all([
        youtubeAPI.searchVideos(params),
        youtubeAPI.getAnalyticsSummary(searchOnlyParams)
      ]);

      setSearchResults(videoResponse.videos || []);
      setFilteredSearchResults(videoResponse.videos || []);
      setTotalResults(videoResponse.total_count || 0);
      setSummaryData(summaryResponse);
      setHasSearched(true);
      
      toast({
        title: "Search completed successfully!",
        description: `Found ${videoResponse.total_count || 0} trending videos matching your criteria.`,
      });
    } catch (error) {
      console.error('Search error:', error);
      
      let errorMessage = "There was an error searching for trending videos. Please try again.";
      if (error.response?.status === 403) {
        errorMessage = "YouTube API quota exceeded. Please try again later.";
      } else if (error.response?.status === 400) {
        errorMessage = "Invalid search parameters. Please check your input.";
      }
      
      toast({
        title: "Search failed",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handlePageChange = (newPage) => {
    if (newPage > 0 && newPage <= Math.ceil(totalResults / pageSize)) {
      handleSearch(currentSearchParams, newPage);
    }
  };

  const calculateSummary = (videos) => {
    if (videos.length === 0) {
      return null;
    }

    const total_videos = videos.length;
    const sentiment_distribution = { positive: 0, negative: 0, neutral: 0 };
    let total_views = 0;
    let total_likes = 0;
    let total_comments = 0;

    for (const video of videos) {
      const sentiment = video.sentiment.toLowerCase();
      if (sentiment in sentiment_distribution) {
        sentiment_distribution[sentiment]++;
      }
      total_views += video.views;
      total_likes += video.likes;
      total_comments += video.comments;
    }

    const overall_sentiment = Object.keys(sentiment_distribution).reduce((a, b) =>
      sentiment_distribution[a] > sentiment_distribution[b] ? a : b
    );

    const average_engagement = {
      views: total_videos > 0 ? total_views / total_videos : 0,
      likes: total_videos > 0 ? total_likes / total_videos : 0,
      comments: total_videos > 0 ? total_comments / total_videos : 0,
    };

    const total_engagement = total_likes + total_comments;

    return {
      total_videos,
      sentiment_distribution,
      overall_sentiment: overall_sentiment.charAt(0).toUpperCase() + overall_sentiment.slice(1),
      average_engagement,
      total_views,
      total_likes,
      total_comments,
      total_engagement,
    };
  };

  const handlePieClick = (sentiment) => {
    setActiveSentiment(sentiment);
    if (sentiment === 'All') {
      setFilteredSearchResults(searchResults);
      setSummaryData(calculateSummary(searchResults));
      setTotalResults(searchResults.length);
    } else {
      const filtered = searchResults.filter(
        (video) => video.sentiment.toLowerCase() === sentiment.toLowerCase()
      );
      setFilteredSearchResults(filtered);
      setSummaryData(calculateSummary(filtered));
      setTotalResults(filtered.length);
    }
  };

  const handleExport = async (format) => {
    if (!currentSearchParams) {
      toast({
        title: "No search data available",
        description: "Please perform a search first before exporting.",
        variant: "destructive",
      });
      return;
    }

    try {
      toast({
        title: `Export ${format.toUpperCase()} started`,
        description: `Your report is being generated in ${format.toUpperCase()} format.`,
      });

      if (format === 'csv') {
        await youtubeAPI.exportCSV(currentSearchParams);
      } else if (format === 'pdf') {
        await youtubeAPI.exportPDF(currentSearchParams);
      }

      toast({
        title: "Export completed!",
        description: `Your ${format.toUpperCase()} report has been downloaded.`,
      });
    } catch (error) {
      console.error('Export error:', error);
      let exportErrorMessage = `There was an error generating the ${format.toUpperCase()} report. Please try again.`;
      if (error.response && error.response.data && error.response.data.detail) {
        exportErrorMessage = error.response.data.detail; // Use detailed message from backend
      }
      toast({
        title: "Export failed",
        description: exportErrorMessage, // Display more specific error
        variant: "destructive",
      });
    }
  };

  return (
    <div className="App min-h-screen bg-gradient-to-br from-gray-50 to-white">
      <Header />
      
      <main className="container mx-auto px-6 py-8">
        {/* Hero Section */}
        <div className="text-center mb-12">
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
            YouTube Trends Analytics
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Discover trending YouTube videos from India and Andhra Pradesh. 
            Analyze engagement metrics, sentiment, and export comprehensive reports.
          </p>
        </div>

        {/* Search Form */}
        <div className="mb-12">
          <SearchForm onSearch={handleSearch} loading={loading} />
        </div>

        {/* Summary */}
        {hasSearched && summaryData && (
          <div className="mb-8">
            <Summary
              summary={summaryData}
              totalResults={totalResults}
              onPieClick={handlePieClick}
            />
          </div>
        )}

        {/* Results */}
        {hasSearched && (
          <div className="mb-8">
            {filteredSearchResults.length > 0 ? (
              <ResultsTable
                data={filteredSearchResults}
                onExport={handleExport}
                onPageChange={handlePageChange}
                currentPage={currentPage}
                totalResults={totalResults}
                pageSize={pageSize}
              />
            ) : (
              <div className="text-center py-12">
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-8 max-w-md mx-auto">
                  <div className="text-yellow-600 mb-4">
                    <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <h3 className="text-lg font-semibold text-yellow-800 mb-2">
                    No Results Found
                  </h3>
                  <p className="text-yellow-700">
                    Try adjusting your search criteria or keywords.
                  </p>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="flex justify-center items-center py-12">
            <div className="text-center">
              <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-red-600 mx-auto mb-4"></div>
              <p className="text-gray-600 text-lg">
                Analyzing YouTube trends...
              </p>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-gray-100 border-t border-gray-200 py-6 mt-12">
        <div className="container mx-auto px-6 text-center">
          <p className="text-gray-600 text-sm">
            For technical clarification reachout to Data Team: Pardhasaradhi
          </p>
        </div>
      </footer>

      <Toaster />
    </div>
  );
}

export default App;
