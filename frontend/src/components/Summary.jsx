import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { BarChart, Users, TrendingUp, Smile, Frown, Meh } from 'lucide-react';
import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const Summary = ({ summary, totalResults, onPieClick }) => {
  if (!summary) {
    return null;
  }

  const {
    sentiment_distribution,
    overall_sentiment,
    average_engagement,
    total_views,
    total_likes,
    total_engagement,
  } = summary;

  const sentimentData = [
    { name: 'Positive', value: sentiment_distribution.positive },
    { name: 'Negative', value: sentiment_distribution.negative },
    { name: 'Neutral', value: sentiment_distribution.neutral },
  ];

  const COLORS = ['#10B981', '#EF4444', '#6B7280'];

  return (
    <Card className="shadow-xl bg-white border-0 mb-8">
      <CardHeader className="bg-gradient-to-r from-blue-50 to-blue-100 rounded-t-lg">
        <CardTitle className="flex items-center space-x-2 text-blue-700">
          <BarChart className="w-6 h-6" />
          <span>Search Summary</span>
        </CardTitle>
      </CardHeader>
      <CardContent className="p-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="lg:col-span-1 flex items-center space-x-4 p-4 bg-gray-50 rounded-lg">
          <div className="bg-blue-100 p-3 rounded-full">
            <Users className="w-6 h-6 text-blue-600" />
          </div>
          <div>
            <p className="text-sm text-gray-600">Total Videos</p>
            <p className="text-2xl font-bold text-gray-900">{totalResults}</p>
          </div>
        </div>
        <div className="lg:col-span-1 flex items-center space-x-4 p-4 bg-gray-50 rounded-lg">
          <div className="bg-yellow-100 p-3 rounded-full">
            <TrendingUp className="w-6 h-6 text-yellow-600" />
          </div>
          <div>
            <p className="text-sm text-gray-600">Overall Sentiment</p>
            <p className="text-2xl font-bold text-gray-900">{overall_sentiment}</p>
          </div>
        </div>
        <div className="lg:col-span-2 row-span-2 flex flex-col items-center justify-center p-4 bg-gray-50 rounded-lg">
          <h3 className="text-lg font-semibold text-gray-800 mb-2">Sentiment Distribution</h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={sentimentData}
                cx="50%"
                cy="50%"
                labelLine={false}
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                onClick={(data) => onPieClick(data.name)}
              >
                {sentimentData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
        <div className="flex items-center space-x-4 p-4 bg-gray-50 rounded-lg">
          <div>
            <p className="text-sm text-gray-600">Avg. Views</p>
            <p className="text-2xl font-bold text-gray-900">{average_engagement.views.toFixed(2)}</p>
          </div>
        </div>
        <div className="flex items-center space-x-4 p-4 bg-gray-50 rounded-lg">
          <div>
            <p className="text-sm text-gray-600">Avg. Likes</p>
            <p className="text-2xl font-bold text-gray-900">{average_engagement.likes.toFixed(2)}</p>
          </div>
        </div>
        <div className="flex items-center space-x-4 p-4 bg-gray-50 rounded-lg">
          <div>
            <p className="text-sm text-gray-600">Avg. Comments</p>
            <p className="text-2xl font-bold text-gray-900">{average_engagement.comments.toFixed(2)}</p>
          </div>
        </div>
        <div className="flex items-center space-x-4 p-4 bg-gray-50 rounded-lg">
          <div>
            <p className="text-sm text-gray-600">Total Views</p>
            <p className="text-2xl font-bold text-gray-900">{total_views}</p>
          </div>
        </div>
        <div className="flex items-center space-x-4 p-4 bg-gray-50 rounded-lg">
          <div>
            <p className="text-sm text-gray-600">Total Likes</p>
            <p className="text-2xl font-bold text-gray-900">{total_likes}</p>
          </div>
        </div>
        <div className="flex items-center space-x-4 p-4 bg-gray-50 rounded-lg">
          <div>
            <p className="text-sm text-gray-600">Total Engagement</p>
            <p className="text-2xl font-bold text-gray-900">{total_engagement}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default Summary;
