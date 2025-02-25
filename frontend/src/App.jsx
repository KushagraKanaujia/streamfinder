import { useState, useEffect } from 'react'
import FilterWizard from './components/FilterWizard'
import RecommendationCard from './components/RecommendationCard'
import LoadingState from './components/LoadingState'

function App() {
  const [recommendations, setRecommendations] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [sessionId] = useState(() => Math.random().toString(36).substring(7))
  const [showResults, setShowResults] = useState(false)

  // Check backend health on mount
  useEffect(() => {
    fetch('/api/health')
      .then((res) => res.json())
      .then((data) => console.log('Backend connected:', data))
      .catch(() => console.warn('Backend not available'))
  }, [])

  const handleGetRecommendations = async ({ category, searchQuery, region }) => {
    setLoading(true)
    setError(null)
    setShowResults(true)

    try {
      const response = await fetch('/api/recommendations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          category,
          searchQuery,
          region,
          limit: 20,
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to fetch recommendations')
      }

      const data = await response.json()
      setRecommendations(data.results)

      // Log the interaction
      logInteraction({
        category,
        searchQuery,
        region,
        recommendations: data.results.map((r) => r.id),
      })
    } catch (err) {
      setError('Something went wrong. Please try again.')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleVideoClick = (videoId, position) => {
    // Log the click
    logInteraction({
      category: recommendations[0]?.platform || 'unknown',
      searchQuery: '',
      region: 'US',
      recommendations: recommendations.map((r) => r.id),
      clicked_video_id: videoId,
      clicked_position: position,
    })
  }

  const logInteraction = async (data) => {
    try {
      await fetch('/api/interactions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...data,
          session_id: sessionId,
        }),
      })
    } catch (err) {
      // Fail silently - logging is not critical
      console.warn('Failed to log interaction:', err)
    }
  }

  const handleStartOver = () => {
    setShowResults(false)
    setRecommendations([])
    setError(null)
  }

  return (
    <div className="min-h-screen relative overflow-hidden">
      {/* Animated Background */}
      <div className="absolute inset-0 bg-gradient-to-br from-gray-900 via-purple-900/20 to-gray-900"></div>
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-purple-600/20 via-transparent to-transparent"></div>

      <div className="relative z-10">
        <div className="max-w-7xl mx-auto px-4 py-8">
          {/* Header */}
          {!showResults && (
            <header className="text-center pt-20 pb-16">
              <div className="mb-6 inline-block">
                <div className="relative">
                  <div className="absolute inset-0 blur-3xl bg-gradient-to-r from-primary via-pink-500 to-purple-500 opacity-20 animate-pulse"></div>
                  <h1 className="relative text-7xl md:text-8xl font-black mb-6 bg-gradient-to-r from-primary via-pink-500 to-purple-500 bg-clip-text text-transparent tracking-tight">
                    StreamFinder
                  </h1>
                </div>
              </div>
              <p className="text-gray-300 text-xl md:text-2xl font-light max-w-2xl mx-auto mb-4">
                Discover movies, shows, shorts & reels across all streaming platforms
              </p>
              <div className="flex items-center justify-center gap-4 text-gray-400 text-sm">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                  <span>Netflix</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                  <span>Prime</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-purple-500 rounded-full animate-pulse"></div>
                  <span>HBO</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
                  <span>YouTube</span>
                </div>
              </div>
            </header>
          )}

          {/* Wizard or Results */}
          {!showResults ? (
            <div className="max-w-4xl mx-auto">
              <FilterWizard onSubmit={handleGetRecommendations} />
            </div>
          ) : (
            <div>
              {/* Results Header */}
              <div className="flex items-center justify-between mb-8 pt-8">
                <button
                  type="button"
                  onClick={(e) => {
                    e.preventDefault()
                    handleStartOver()
                  }}
                  className="group flex items-center gap-3 bg-gradient-to-r from-gray-800 to-gray-700 hover:from-gray-700 hover:to-gray-600 px-6 py-3 rounded-full transition-all shadow-lg hover:shadow-xl"
                >
                  <svg
                    className="w-5 h-5 group-hover:-translate-x-1 transition-transform"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M10 19l-7-7m0 0l7-7m-7 7h18"
                    />
                  </svg>
                  <span className="font-semibold">New Search</span>
                </button>

                {!loading && recommendations.length > 0 && (
                  <div className="flex items-center gap-3 bg-gray-800/50 backdrop-blur px-5 py-3 rounded-full">
                    <svg className="w-5 h-5 text-primary" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z"/>
                      <path fillRule="evenodd" d="M4 5a2 2 0 012-2 3 3 0 003 3h2a3 3 0 003-3 2 2 0 012 2v11a2 2 0 01-2 2H6a2 2 0 01-2-2V5zm3 4a1 1 0 000 2h.01a1 1 0 100-2H7zm3 0a1 1 0 000 2h3a1 1 0 100-2h-3zm-3 4a1 1 0 100 2h.01a1 1 0 100-2H7zm3 0a1 1 0 100 2h3a1 1 0 100-2h-3z" clipRule="evenodd"/>
                    </svg>
                    <span className="text-white font-semibold">{recommendations.length} Results</span>
                  </div>
                )}
              </div>

              {/* Error State */}
              {error && (
                <div className="bg-red-500/10 border-2 border-red-500 text-red-200 px-6 py-4 rounded-2xl mb-8 backdrop-blur">
                  <div className="flex items-center gap-3">
                    <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd"/>
                    </svg>
                    {error}
                  </div>
                </div>
              )}

              {/* Loading State */}
              {loading && <LoadingState />}

              {/* Results Grid */}
              {!loading && recommendations.length > 0 && (
                <div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                    {recommendations.map((video, index) => (
                      <RecommendationCard
                        key={video.id}
                        video={video}
                        position={index}
                        onClick={handleVideoClick}
                      />
                    ))}
                  </div>
                </div>
              )}

              {/* No Results */}
              {!loading && recommendations.length === 0 && !error && (
                <div className="text-center py-20">
                  <div className="mb-4">
                    <svg className="w-20 h-20 mx-auto text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                    </svg>
                  </div>
                  <p className="text-gray-400 text-xl mb-2">No results found</p>
                  <p className="text-gray-500">Try searching for something else</p>
                </div>
              )}
            </div>
          )}

          {/* Footer */}
          <footer className="text-center mt-20 pb-8">
            <div className="inline-flex items-center gap-3 text-gray-500 text-sm bg-gray-800/30 backdrop-blur px-6 py-3 rounded-full">
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path d="M11 3a1 1 0 10-2 0v1a1 1 0 102 0V3zM15.657 5.757a1 1 0 00-1.414-1.414l-.707.707a1 1 0 001.414 1.414l.707-.707zM18 10a1 1 0 01-1 1h-1a1 1 0 110-2h1a1 1 0 011 1zM5.05 6.464A1 1 0 106.464 5.05l-.707-.707a1 1 0 00-1.414 1.414l.707.707zM5 10a1 1 0 01-1 1H3a1 1 0 110-2h1a1 1 0 011 1zM8 16v-1h4v1a2 2 0 11-4 0zM12 14c.015-.34.208-.646.477-.859a4 4 0 10-4.954 0c.27.213.462.519.476.859h4.002z"/>
              </svg>
              <span>Powered by TMDB & YouTube Data API</span>
            </div>
          </footer>
        </div>
      </div>
    </div>
  )
}

export default App
