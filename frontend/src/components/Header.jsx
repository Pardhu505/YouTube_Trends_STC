import React from 'react';

const Header = () => {
  return (
    <header className="bg-white shadow-lg border-b-2 border-gray-100">
      <div className="container mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          {/* Company Logo */}
          <div className="flex items-center space-x-4">
            <img 
              alt="ShowTime Consulting" 
              className="h-12 w-auto" 
              src="https://showtimeconsulting.in/images/settings/2fd13f50.png"
            />
            <div className="text-gray-800">
              <h1 className="text-xl font-bold">ShowTime Consulting</h1>
              <p className="text-gray-600 text-sm">YouTube Trends Analytics</p>
            </div>
          </div>

          {/* YouTube Branding */}
          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-2 bg-red-50 border border-red-200 rounded-full px-4 py-2">
              <svg className="w-8 h-8 text-red-600" viewBox="0 0 24 24" fill="currentColor">
                <path d="M23.498 6.186a2.97 2.97 0 0 0-2.089-2.089C19.706 3.5 12 3.5 12 3.5s-7.706 0-9.409.597A2.97 2.97 0 0 0 .502 6.186C0 7.889 0 12 0 12s0 4.111.502 5.814a2.97 2.97 0 0 0 2.089 2.089C4.294 20.5 12 20.5 12 20.5s7.706 0 9.409-.597a2.97 2.97 0 0 0 2.089-2.089C24 16.111 24 12 24 12s0-4.111-.502-5.814ZM9.75 15.568V8.432L15.818 12l-6.068 3.568Z"/>
              </svg>
              <span className="text-red-800 font-semibold">Powered by YouTube</span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;