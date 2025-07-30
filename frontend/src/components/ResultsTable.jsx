import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from './ui/table';
import { 
  Download, 
  FileText, 
  Eye, 
  ThumbsUp, 
  MessageCircle,
  ExternalLink,
  Calendar,
  TrendingUp
} from 'lucide-react';

const ResultsTable = ({ data, onExport, onPageChange, currentPage, totalResults, pageSize }) => {
  const [sortField, setSortField] = useState('views');
  const [sortOrder, setSortOrder] = useState('desc');

  const totalPages = Math.ceil(totalResults / pageSize);

  const formatNumber = (num) => {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
  };

  const getSentimentColor = (sentiment) => {
    switch (sentiment.toLowerCase()) {
      case 'positive':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'negative':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'neutral':
        return 'bg-gray-100 text-gray-800 border-gray-200';
      default:
        return 'bg-blue-100 text-blue-800 border-blue-200';
    }
  };

  const sortedData = [...data].sort((a, b) => {
    const aValue = a[sortField];
    const bValue = b[sortField];
    
    if (sortOrder === 'asc') {
      return aValue > bValue ? 1 : -1;
    } else {
      return aValue < bValue ? 1 : -1;
    }
  });

  return (
    <Card className="shadow-xl bg-white border-0">
      <CardHeader className="bg-gradient-to-r from-red-50 to-red-100 rounded-t-lg">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center space-x-2 text-red-700">
            <TrendingUp className="w-6 h-6" />
            <span>YouTube Trends Analysis Results</span>
          </CardTitle>
          <div className="flex space-x-2">
            <Button
              onClick={() => onExport('csv')}
              variant="outline"
              size="sm"
              className="border-red-300 text-red-700 hover:bg-red-50"
            >
              <FileText className="w-4 h-4 mr-2" />
              Export CSV
            </Button>
            <Button
              onClick={() => onExport('pdf')}
              variant="outline"
              size="sm"
              className="border-red-300 text-red-700 hover:bg-red-50"
            >
              <Download className="w-4 h-4 mr-2" />
              Export PDF
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow className="bg-gray-50">
                <TableHead className="font-semibold text-gray-700 text-center">
                  <div className="flex items-center justify-center space-x-1">
                    <Calendar className="w-4 h-4" />
                    <span>Timestamp</span>
                  </div>
                </TableHead>
                <TableHead className="font-semibold text-gray-700 text-center">Video Content</TableHead>
                <TableHead className="font-semibold text-gray-700 text-center">
                  <div className="flex items-center justify-center space-x-1 cursor-pointer" onClick={() => {
                    setSortField('views');
                    setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
                  }}>
                    <Eye className="w-4 h-4" />
                    <span>Views</span>
                  </div>
                </TableHead>
                <TableHead className="font-semibold text-gray-700 text-center">
                  <div className="flex items-center justify-center space-x-1">
                    <ThumbsUp className="w-4 h-4" />
                    <span>Likes</span>
                  </div>
                </TableHead>
                <TableHead className="font-semibold text-gray-700 text-center">
                  <div className="flex items-center justify-center space-x-1">
                    <MessageCircle className="w-4 h-4" />
                    <span>Comments</span>
                  </div>
                </TableHead>
                <TableHead className="font-semibold text-gray-700 text-center">Sentiment</TableHead>
                <TableHead className="font-semibold text-gray-700 text-center">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {sortedData.map((video, index) => (
                <TableRow key={index} className="hover:bg-gray-50 transition-colors">
                  <TableCell className="font-medium text-center">
                    {new Date(video.timestamp).toLocaleDateString('en-IN', {
                      year: 'numeric',
                      month: 'short',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit'
                    })}
                  </TableCell>
                  <TableCell className="text-center">
                    <div className="flex items-center justify-center space-x-3">
                      <img
                        src={video.thumbnail}
                        alt={video.title}
                        className="w-16 h-12 object-cover rounded-lg shadow-sm"
                      />
                      <div className="flex-1 min-w-0 text-left">
                        <h4 className="font-medium text-gray-900 truncate">
                          {video.title}
                        </h4>
                        <p className="text-sm text-gray-600 mt-1">
                          {video.channel}
                        </p>
                        <p className="text-xs text-gray-500 mt-1 line-clamp-2">
                          {video.description}
                        </p>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell className="font-semibold text-red-600 text-center">
                    {formatNumber(video.views)}
                  </TableCell>
                  <TableCell className="font-medium text-green-600 text-center">
                    {formatNumber(video.likes)}
                  </TableCell>
                  <TableCell className="font-medium text-blue-600 text-center">
                    {formatNumber(video.comments)}
                  </TableCell>
                  <TableCell className="text-center">
                    <div className="flex justify-center">
                      <Badge className={`${getSentimentColor(video.sentiment)} font-medium`}>
                        {video.sentiment}
                      </Badge>
                    </div>
                  </TableCell>
                  <TableCell className="text-center">
                    <div className="flex justify-center">
                      <Button
                        size="sm"
                        variant="outline"
                        className="text-red-600 border-red-300 hover:bg-red-50"
                        onClick={() => window.open(video.url, '_blank')}
                      >
                        <ExternalLink className="w-4 h-4 mr-1" />
                        View
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </CardContent>
      <div className="flex items-center justify-between p-4 border-t">
        <div>
          <p className="text-sm text-gray-700">
            Showing{' '}
            <span className="font-medium">
              {Math.min(1 + (currentPage - 1) * pageSize, totalResults)}
            </span>{' '}
            to{' '}
            <span className="font-medium">
              {Math.min(currentPage * pageSize, totalResults)}
            </span>{' '}
            of <span className="font-medium">{totalResults}</span> results
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => onPageChange(currentPage - 1)}
            disabled={currentPage === 1}
          >
            <ChevronLeft className="w-4 h-4" />
            Previous
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => onPageChange(currentPage + 1)}
            disabled={currentPage === totalPages}
          >
            Next
            <ChevronRight className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </Card>
  );
};

export default ResultsTable;