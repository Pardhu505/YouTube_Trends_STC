import React, { useState, useEffect } from 'react';
import './App.css';
import Header from './components/Header';
import SearchForm from './components/SearchForm';
import ResultsTable from './components/ResultsTable';
import { youtubeAPI } from './services/api';
import { useToast } from './hooks/use-toast';
import { Toaster } from './components/ui/sonner';

function App() {
  const [searchResults, setSearchResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [currentSearchParams, setCurrentSearchParams] = useState(null);
  const { toast } = useToast();

  // Aggressive Emergent branding removal
  useEffect(() => {
    const removeEmergentBranding = () => {
      // Target the specific emergent badge by ID
      const emergentBadge = document.getElementById('emergent-badge');
      if (emergentBadge) {
        emergentBadge.remove();
      }

      // Target by href attribute
      const emergentLinks = document.querySelectorAll('a[href*="emergent.sh"], a[href*="utm_source=emergent-badge"]');
      emergentLinks.forEach(link => link.remove());

      // Target elements with specific styling patterns matching the badge
      const allElements = document.querySelectorAll('*');
      allElements.forEach(element => {
        const style = window.getComputedStyle(element);
        const text = element.textContent || '';
        
        // Check for the specific emergent badge pattern
        if (text.includes('Made with Emergent') && 
            style.position === 'fixed' && 
            style.zIndex === '9999') {
          element.remove();
        }

        // Remove elements with emergent-specific attributes
        if (element.id && element.id.includes('emergent')) {
          element.remove();
        }

        // Remove any fixed positioned elements in bottom-right with emergent content
        if (style.position === 'fixed' && 
            style.bottom && 
            style.right && 
            text.includes('Emergent')) {
          element.remove();
        }
      });

      // Hide any remaining emergent elements
      document.querySelectorAll('*').forEach(element => {
        if (element.textContent && element.textContent.includes('Made with Emergent')) {
          element.style.display = 'none';
          element.style.visibility = 'hidden';
          element.style.opacity = '0';
          element.style.pointerEvents = 'none';
        }
      });
    };

    // Run immediately
    removeEmergentBranding();

    // Run every 500ms to catch dynamically added elements
    const interval = setInterval(removeEmergentBranding, 500);

    // Run when DOM changes
    const observer = new MutationObserver(removeEmergentBranding);
    observer.observe(document.body, { 
      childList: true, 
      subtree: true,
      attributes: true,
      attributeOldValue: true
    });

    // Run on window load to catch late-loading elements
    window.addEventListener('load', removeEmergentBranding);

    return () => {
      clearInterval(interval);
      observer.disconnect();
      window.removeEventListener('load', removeEmergentBranding);
    };
  }, []);

  const handleSearch = async (searchParams) => {
    setLoading(true);
    setCurrentSearchParams(searchParams);
    
    try {
      const response = await youtubeAPI.searchVideos(searchParams);
      setSearchResults(response.videos || []);
      setHasSearched(true);
      
      toast({
        title: "Search completed successfully!",
        description: `Found ${response.total_count || 0} trending videos matching your criteria.`,
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
      toast({
        title: "Export failed",
        description: `There was an error generating the ${format.toUpperCase()} report. Please try again.`,
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

        {/* Results */}
        {hasSearched && (
          <div className="mb-8">
            {searchResults.length > 0 ? (
              <ResultsTable data={searchResults} onExport={handleExport} />
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
            For technical clarification reachout to Data Team: Prdhasaradhi
          </p>
        </div>
      </footer>

      <Toaster />
    </div>
  );
}

export default App;