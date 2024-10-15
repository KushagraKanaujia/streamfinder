import { useState, useEffect } from 'react'

const PLATFORMS = {
  netflix: { name: 'NETFLIX', color: 'bg-red-600' },
  prime: { name: 'PRIME', color: 'bg-blue-600' },
  disney: { name: 'DISNEY+', color: 'bg-blue-500' },
  hulu: { name: 'HULU', color: 'bg-green-600' },
  hbo: { name: 'HBO MAX', color: 'bg-purple-600' },
  apple: { name: 'APPLE TV+', color: 'bg-gray-700' },
  peacock: { name: 'PEACOCK', color: 'bg-yellow-600' },
  tiktok: { name: 'TIKTOK', color: 'bg-black' },
  youtube: { name: 'YOUTUBE', color: 'bg-red-600' },
  shorts: { name: 'SHORTS', color: 'bg-red-500' },
  movies: { name: 'MOVIE', color: 'bg-primary' },
  tv: { name: 'TV SHOW', color: 'bg-primary' },
}

const getWatchlist = () => JSON.parse(localStorage.getItem('watchlist') || '[]')
const saveWatchlist = (list) => localStorage.setItem('watchlist', JSON.stringify(list))

export default function RecommendationCard({ video, position, onClick }) {
  const [isInWatchlist, setIsInWatchlist] = useState(false)
  const [showDetails, setShowDetails] = useState(false)

  useEffect(() => {
    setIsInWatchlist(getWatchlist().some(item => item.id === video.id))
  }, [video.id])

  const handleClick = () => {
    onClick(video.id, position)
    window.open(video.url, '_blank')
  }

  const toggleWatchlist = (e) => {
    e.stopPropagation()
    const watchlist = getWatchlist()

    if (isInWatchlist) {
      saveWatchlist(watchlist.filter(item => item.id !== video.id))
      setIsInWatchlist(false)
    } else {
      saveWatchlist([...watchlist, video])
      setIsInWatchlist(true)
    }
  }

  const getPlatformColor = (platform) => PLATFORMS[platform]?.color || 'bg-primary'
  const getPlatformName = (platform) => PLATFORMS[platform]?.name || platform.toUpperCase()

  return (
    <div
      onClick={handleClick}
      onMouseEnter={() => setShowDetails(true)}
      onMouseLeave={() => setShowDetails(false)}
      className="bg-gray-800 rounded-xl overflow-hidden hover:scale-105 hover:shadow-2xl transition-all duration-300 cursor-pointer group animate-fade-in relative"
    >
      <div className="relative">
        <img
          src={video.thumbnail}
          alt={video.title}
          className="w-full h-56 object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black via-transparent to-transparent opacity-60"></div>
        <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-50 transition-all flex items-center justify-center">
          <svg
            className="w-20 h-20 text-white opacity-0 group-hover:opacity-100 transition-opacity drop-shadow-lg"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path d="M6.3 2.841A1.5 1.5 0 004 4.11V15.89a1.5 1.5 0 002.3 1.269l9.344-5.89a1.5 1.5 0 000-2.538L6.3 2.84z" />
          </svg>
        </div>

        {/* Rating badge */}
        {video.rating > 0 && (
          <div className="absolute top-3 left-3 flex items-center gap-1 bg-black/80 backdrop-blur-sm px-2.5 py-1.5 rounded-lg">
            <svg className="w-4 h-4 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
              <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
            </svg>
            <span className="text-white font-bold text-sm">{video.rating}</span>
          </div>
        )}

        {/* Watchlist button */}
        <button
          onClick={toggleWatchlist}
          className="absolute top-3 right-14 bg-black/80 backdrop-blur-sm p-2 rounded-lg hover:scale-110 transition-transform z-10"
          title={isInWatchlist ? "Remove from watchlist" : "Add to watchlist"}
        >
          <svg className="w-5 h-5" fill={isInWatchlist ? "currentColor" : "none"} stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" className={isInWatchlist ? "text-red-500" : "text-white"} />
          </svg>
        </button>

        {/* Primary platform badge */}
        <span className={`absolute top-3 right-3 px-3 py-1.5 rounded-md text-xs font-bold shadow-lg ${getPlatformColor(video.platform)}`}>
          {getPlatformName(video.platform)}
        </span>

        {/* Additional platforms (if available) */}
        {video.all_platforms && video.all_platforms.length > 1 && (
          <div className="absolute bottom-3 left-3 flex gap-1.5">
            {video.all_platforms.slice(0, 4).map((platform, idx) => (
              <span
                key={idx}
                className={`px-2 py-1 rounded text-xs font-semibold ${getPlatformColor(platform)} opacity-90`}
                title={getPlatformName(platform)}
              >
                {getPlatformName(platform).slice(0, 3)}
              </span>
            ))}
            {video.all_platforms.length > 4 && (
              <span className="px-2 py-1 rounded text-xs font-semibold bg-gray-700 opacity-90">
                +{video.all_platforms.length - 4}
              </span>
            )}
          </div>
        )}
      </div>
      <div className="p-4">
        <div className="flex items-start justify-between gap-2 mb-2">
          <h3 className="font-bold text-white line-clamp-2 text-lg flex-1">
            {video.title}
          </h3>
          {video.year && (
            <span className="text-gray-400 text-sm font-semibold shrink-0 mt-0.5">
              {video.year}
            </span>
          )}
        </div>
        {video.description && (
          <p className="text-gray-400 text-sm line-clamp-2 mb-2">{video.description}</p>
        )}
        <div className="flex items-center justify-between">
          <p className="text-gray-500 text-xs">{video.channel}</p>
          <span className="text-primary text-xs font-semibold">Watch Now →</span>
        </div>
      </div>

      {/* Hover Details Overlay */}
      {showDetails && video.description && (
        <div className="absolute inset-0 bg-gradient-to-t from-black via-black/95 to-black/90 p-5 flex flex-col justify-end animate-fade-in z-20 rounded-xl">
          <div className="flex items-start justify-between gap-2 mb-3">
            <h3 className="font-bold text-white text-xl">
              {video.title}
            </h3>
            {video.year && (
              <span className="text-gray-300 text-base font-semibold shrink-0">
                {video.year}
              </span>
            )}
          </div>

          {video.rating > 0 && (
            <div className="flex items-center gap-2 mb-3">
              <div className="flex items-center gap-1">
                <svg className="w-5 h-5 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                </svg>
                <span className="text-white font-bold text-base">{video.rating}/10</span>
              </div>
            </div>
          )}

          <p className="text-gray-300 text-sm mb-4 line-clamp-4">{video.description}</p>

          {video.all_platforms && video.all_platforms.length > 0 && (
            <div className="mb-3">
              <p className="text-gray-400 text-xs mb-2">Available on:</p>
              <div className="flex flex-wrap gap-2">
                {video.all_platforms.map((platform, idx) => (
                  <span
                    key={idx}
                    className={`px-2.5 py-1 rounded-md text-xs font-semibold ${getPlatformColor(platform)}`}
                  >
                    {getPlatformName(platform)}
                  </span>
                ))}
              </div>
            </div>
          )}

          <div className="flex items-center gap-3">
            <span className="text-primary text-sm font-bold flex items-center gap-1">
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" />
              </svg>
              Click to Watch
            </span>
          </div>
        </div>
      )}
    </div>
  )
}
