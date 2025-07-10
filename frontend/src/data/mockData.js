// Mock YouTube trends data for Andhra Pradesh/Telugu content
export const mockYouTubeData = [
  {
    id: '1',
    title: 'Pushpa 2 The Rule Official Trailer | Allu Arjun | Sukumar',
    channel: 'Mythri Movie Makers',
    description: 'The much-awaited sequel to the blockbuster Pushpa movie. Allu Arjun returns as Pushpa Raj in this action-packed thriller.',
    thumbnail: 'https://i.ytimg.com/vi/AnOG4Tl_8Ws/hqdefault.jpg',
    url: 'https://www.youtube.com/watch?v=AnOG4Tl_8Ws',
    views: 45670000,
    likes: 1234567,
    comments: 89012,
    timestamp: '2024-07-15T10:30:00Z',
    sentiment: 'Positive',
    source: 'YouTube'
  },
  {
    id: '2',
    title: 'Devara Movie Review | Jr NTR | Koratala Siva | Telugu Cinema',
    channel: 'Telugu Cinema Review',
    description: 'Complete review of Devara movie starring Jr NTR. Analysis of story, performances, and technical aspects.',
    thumbnail: 'https://i.ytimg.com/vi/kOHB85vDuow/hqdefault.jpg',
    url: 'https://www.youtube.com/watch?v=kOHB85vDuow',
    views: 23450000,
    likes: 567890,
    comments: 45678,
    timestamp: '2024-07-14T15:45:00Z',
    sentiment: 'Positive',
    source: 'YouTube'
  },
  {
    id: '3',
    title: 'Kalki 2898 AD Box Office Collection | Prabhas | Telugu Movies',
    channel: 'Box Office Telugu',
    description: 'Latest box office collection update of Kalki 2898 AD. Prabhas starrer continues to break records.',
    thumbnail: 'https://i.ytimg.com/vi/YEIlw2LTCl0/hqdefault.jpg',
    url: 'https://www.youtube.com/watch?v=YEIlw2LTCl0',
    views: 18900000,
    likes: 456789,
    comments: 34567,
    timestamp: '2024-07-13T12:20:00Z',
    sentiment: 'Positive',
    source: 'YouTube'
  },
  {
    id: '4',
    title: 'Bigg Boss Telugu Season 8 Latest Episode | Nagarjuna',
    channel: 'Star Maa',
    description: 'Latest episode of Bigg Boss Telugu Season 8 hosted by Nagarjuna. Drama, tasks, and eliminations.',
    thumbnail: 'https://i.ytimg.com/vi/pNJJd5YQCT8/hqdefault.jpg',
    url: 'https://www.youtube.com/watch?v=pNJJd5YQCT8',
    views: 12340000,
    likes: 234567,
    comments: 78901,
    timestamp: '2024-07-12T20:00:00Z',
    sentiment: 'Neutral',
    source: 'YouTube'
  },
  {
    id: '5',
    title: 'Vijayawada Floods Update | Andhra Pradesh News | Telugu News',
    channel: 'TV9 Telugu',
    description: 'Latest updates on Vijayawada floods situation. Government response and relief measures.',
    thumbnail: 'https://i.ytimg.com/vi/PNJJd5YQCT8/hqdefault.jpg',
    url: 'https://www.youtube.com/watch?v=PNJJd5YQCT8',
    views: 8760000,
    likes: 123456,
    comments: 56789,
    timestamp: '2024-07-11T18:30:00Z',
    sentiment: 'Negative',
    source: 'YouTube'
  },
  {
    id: '6',
    title: 'Chiranjeevi Dance Performance | Mega Star | Telugu Songs',
    channel: 'Mega Fans Club',
    description: 'Chiranjeevi\'s iconic dance performance compilation. Best moments from the Mega Star\'s career.',
    thumbnail: 'https://i.ytimg.com/vi/QNJJd5YQCT8/hqdefault.jpg',
    url: 'https://www.youtube.com/watch?v=QNJJd5YQCT8',
    views: 15670000,
    likes: 789012,
    comments: 23456,
    timestamp: '2024-07-10T14:15:00Z',
    sentiment: 'Positive',
    source: 'YouTube'
  },
  {
    id: '7',
    title: 'Hyderabad Traffic Problems | Telangana News | City Updates',
    channel: 'Telangana Today',
    description: 'Analysis of growing traffic problems in Hyderabad. Solutions and government initiatives.',
    thumbnail: 'https://i.ytimg.com/vi/RNJJd5YQCT8/hqdefault.jpg',
    url: 'https://www.youtube.com/watch?v=RNJJd5YQCT8',
    views: 5430000,
    likes: 98765,
    comments: 12345,
    timestamp: '2024-07-09T09:45:00Z',
    sentiment: 'Negative',
    source: 'YouTube'
  },
  {
    id: '8',
    title: 'Telugu Tech Tips | Smartphone Reviews | Technology Telugu',
    channel: 'Telugu Tech Guru',
    description: 'Latest smartphone reviews and tech tips in Telugu. Gadget reviews for Telugu audience.',
    thumbnail: 'https://i.ytimg.com/vi/SNJJd5YQCT8/hqdefault.jpg',
    url: 'https://www.youtube.com/watch?v=SNJJd5YQCT8',
    views: 9870000,
    likes: 456789,
    comments: 67890,
    timestamp: '2024-07-08T16:20:00Z',
    sentiment: 'Positive',
    source: 'YouTube'
  }
];

// Mock search function
export const mockSearch = (searchParams) => {
  return new Promise((resolve) => {
    setTimeout(() => {
      // Filter data based on search params (mock implementation)
      let filteredData = mockYouTubeData;
      
      if (searchParams.keywords) {
        const keywords = searchParams.keywords.toLowerCase();
        filteredData = filteredData.filter(video => 
          video.title.toLowerCase().includes(keywords) ||
          video.description.toLowerCase().includes(keywords) ||
          video.channel.toLowerCase().includes(keywords)
        );
      }
      
      resolve(filteredData);
    }, 2000); // Simulate API delay
  });
};