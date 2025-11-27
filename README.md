# StreamFinder

A video search tool that helps you discover movies, TV shows, YouTube videos, shorts, and reels across multiple streaming platforms - all in one place.

## 🔗 Live Demo

**[Try StreamFinder Live](https://streamfinder-app.vercel.app)**

## What It Does

StreamFinder aggregates video content from various sources and provides intelligent recommendations based on your search. Whether you're looking for movies on Netflix, shows on Prime Video, or trending YouTube content, StreamFinder finds similar content across all platforms.

**Search across:**
- Streaming platforms: Netflix, Prime Video, Disney+, HBO Max, Hulu, Apple TV+
- YouTube: Videos, Shorts, trending content
- Movies and TV shows with detailed metadata

## Features

- **Smart Recommendations**: Multi-factor algorithm that considers genre, cast, director, ratings, and more
- **Platform Detection**: Automatically finds where content is available to stream
- **Watchlist**: Save videos to watch later (stored locally in your browser)
- **Detailed Info**: Hover over any video to see full details including ratings, runtime, and synopsis
- **Fast Search**: Cached results for quick repeated searches
- **Clean UI**: Modern, responsive design that works on desktop and mobile

## Tech Stack

**Backend:**
- FastAPI (Python web framework)
- SQLAlchemy (Database ORM)
- TMDB API (Movie/TV data)
- YouTube Data API v3 (Video content)

**Frontend:**
- React 18 with Vite
- Tailwind CSS
- LocalStorage for watchlist

## Getting Started

### Prerequisites

- Python 3.9+
- Node.js 18+
- TMDB API Key ([Get one here](https://www.themoviedb.org/settings/api))
- YouTube Data API Key ([Get one here](https://console.cloud.google.com/apis/library/youtube.googleapis.com))

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/KushagraKanaujia/streamfinder.git
cd streamfinder
```

2. **Set up the Backend**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **Configure API Keys**
Create a `.env` file in the `backend` directory:
```bash
TMDB_API_KEY=your_tmdb_api_key_here
YOUTUBE_API_KEY=your_youtube_api_key_here
```

4. **Run the Backend**
```bash
uvicorn app.main:app --reload --port 8000
```

The backend will start at `http://localhost:8000`

5. **Set up the Frontend** (in a new terminal)
```bash
cd frontend
npm install
npm run dev
```

The frontend will start at `http://localhost:5173`

6. **Open in Browser**
Visit `http://localhost:5173` and start searching for videos!

## How to Use

1. Choose a category (Movies, TV Shows, YouTube Videos, or Shorts/Reels)
2. Enter a search term or select from trending options
3. Select your region (US, UK, IN, etc.)
4. Click "Find Content" to get recommendations
5. Click on any video card to visit the platform or watch
6. Add videos to your watchlist for later

## API Endpoints

The backend provides the following endpoints:

- `POST /api/recommendations` - Get video recommendations
- `POST /api/interactions` - Log user interactions
- `GET /api/health` - Health check

Full API documentation available at `http://localhost:8000/docs` when running locally.

## Project Structure

```
streamfinder/
├── backend/
│   ├── app/
│   │   ├── main.py         # FastAPI application
│   │   ├── config.py       # Configuration
│   │   ├── database.py     # Database setup
│   │   ├── models.py       # Data models
│   │   ├── routes.py       # API endpoints
│   │   └── services.py     # Recommendation logic
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
└── README.md
```

## How It Works

1. **Search**: You enter what you're looking for (e.g., "action movies", "comedy shows", "tech reviews")
2. **Aggregation**: The backend queries TMDB and YouTube APIs simultaneously
3. **Recommendation**: Content is scored based on relevance, ratings, popularity, and similarity
4. **Results**: You get a unified list of videos across all platforms with links to watch

## Troubleshooting

**Backend won't start:**
- Make sure you've activated the virtual environment
- Check that API keys are set in `.env` file
- Verify Python 3.9+ is installed: `python3 --version`

**Frontend won't start:**
- Make sure Node.js 18+ is installed: `node --version`
- Try deleting `node_modules` and running `npm install` again
- Check that the backend is running on port 8000

**No results showing:**
- Verify both TMDB and YouTube API keys are valid
- Check browser console for errors (F12)
- Make sure backend terminal shows successful API responses

## License

MIT License - Feel free to use this project for learning or personal use.

## Acknowledgments

- TMDB for movie and TV show data
- YouTube Data API for video content
- Built with FastAPI, React, and Tailwind CSS

## 📊 Analytics

Track your streaming habits with built-in analytics:
- Most searched genres
- Platform usage statistics
- Watch history
