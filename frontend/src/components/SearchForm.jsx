import React, { useState } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Calendar, Search, Filter, TrendingUp } from 'lucide-react';

const SearchForm = ({ onSearch, loading }) => {
  const [formData, setFormData] = useState({
    keywords: '',
    startDate: '',
    endDate: '',
    region: 'IN' // India by default
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onSearch(formData);
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  return (
    <Card className="shadow-xl bg-gradient-to-br from-white to-gray-50 border-0">
      <CardHeader className="bg-gradient-to-r from-red-50 to-red-100 rounded-t-lg">
        <CardTitle className="flex items-center space-x-2 text-red-700">
          <TrendingUp className="w-6 h-6" />
          <span>YouTube Trends Search</span>
        </CardTitle>
      </CardHeader>
      <CardContent className="p-6">
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Keywords Input */}
            <div className="space-y-2">
              <Label htmlFor="keywords" className="text-sm font-semibold text-gray-700">
                Keywords / Hashtags
              </Label>
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                <Input
                  id="keywords"
                  name="keywords"
                  placeholder="e.g., #telugu, movies, entertainment"
                  value={formData.keywords}
                  onChange={handleChange}
                  className="pl-10 border-gray-300 focus:border-red-500 focus:ring-red-500"
                  required
                />
              </div>
            </div>

            {/* Region Selection */}
            <div className="space-y-2">
              <Label htmlFor="region" className="text-sm font-semibold text-gray-700">
                Region
              </Label>
              <select
                id="region"
                name="region"
                value={formData.region}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500"
              >
                <option value="IN">India</option>
                <option value="US">United States</option>
                <option value="GB">United Kingdom</option>
                <option value="CA">Canada</option>
              </select>
            </div>
          </div>

          {/* Date Range */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <Label htmlFor="startDate" className="text-sm font-semibold text-gray-700">
                Start Date
              </Label>
              <div className="relative">
                <Calendar className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                <Input
                  id="startDate"
                  name="startDate"
                  type="date"
                  value={formData.startDate}
                  onChange={handleChange}
                  className="pl-10 border-gray-300 focus:border-red-500 focus:ring-red-500"
                  required
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="endDate" className="text-sm font-semibold text-gray-700">
                End Date
              </Label>
              <div className="relative">
                <Calendar className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                <Input
                  id="endDate"
                  name="endDate"
                  type="date"
                  value={formData.endDate}
                  onChange={handleChange}
                  className="pl-10 border-gray-300 focus:border-red-500 focus:ring-red-500"
                  required
                />
              </div>
            </div>
          </div>

          {/* Submit Button */}
          <div className="flex justify-center pt-4">
            <Button
              type="submit"
              disabled={loading}
              className="bg-gradient-to-r from-red-600 to-red-700 hover:from-red-700 hover:to-red-800 text-white px-8 py-3 rounded-lg font-semibold transform transition-all duration-200 hover:scale-105 shadow-lg hover:shadow-xl"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Analyzing Trends...
                </>
              ) : (
                <>
                  <Filter className="w-4 h-4 mr-2" />
                  Generate Report
                </>
              )}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
};

export default SearchForm;