import { useState } from 'react'

export default function FilterWizard({ onSubmit }) {
  const [step, setStep] = useState(1)
  const [category, setCategory] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [region, setRegion] = useState('US')

  const categories = [
    {
      id: 'movies',
      name: 'Movies',
      icon: '🎬',
      gradient: 'from-red-500 to-orange-500',
      description: 'Find similar movies',
      placeholder: 'e.g., Avengers, Inception, Interstellar'
    },
    {
      id: 'tv',
      name: 'TV Shows',
      icon: '📺',
      gradient: 'from-blue-500 to-cyan-500',
      description: 'Discover new series',
      placeholder: 'e.g., Breaking Bad, Friends, Stranger Things'
    },
    {
      id: 'youtube',
      name: 'YouTube',
      icon: '▶️',
      gradient: 'from-red-600 to-pink-600',
      description: 'Trending videos & creators',
      placeholder: 'e.g., MrBeast, cooking tutorials, tech reviews'
    },
    {
      id: 'tiktok',
      name: 'Shorts & Reels',
      icon: '📱',
      gradient: 'from-purple-500 to-pink-500',
      description: 'Viral short-form content',
      placeholder: 'e.g., labubu, dance trends, funny cats'
    },
  ]

  const handleCategorySelect = (cat) => {
    setCategory(cat)
    setSearchQuery('')
    setStep(2)
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!searchQuery.trim()) return

    onSubmit({
      category,
      searchQuery: searchQuery.trim(),
      region
    })
  }

  const handleReset = () => {
    setStep(1)
    setCategory('')
    setSearchQuery('')
  }

  const getCategoryInfo = () => {
    return categories.find(c => c.id === category)
  }

  return (
    <div className="max-w-4xl mx-auto">
      {/* Progress Bar */}
      <div className="mb-8">
        <div className="flex items-center justify-center mb-2">
          <div className="flex items-center">
            <div
              className={`w-10 h-10 rounded-full flex items-center justify-center font-bold ${
                step >= 1 ? 'bg-primary text-white' : 'bg-gray-700 text-gray-400'
              }`}
            >
              1
            </div>
            <div className={`w-20 h-1 mx-2 ${step >= 2 ? 'bg-primary' : 'bg-gray-700'}`}></div>
            <div
              className={`w-10 h-10 rounded-full flex items-center justify-center font-bold ${
                step >= 2 ? 'bg-primary text-white' : 'bg-gray-700 text-gray-400'
              }`}
            >
              2
            </div>
          </div>
        </div>
        <div className="flex justify-center gap-24 text-sm text-gray-400">
          <span>Category</span>
          <span>Search</span>
        </div>
      </div>

      {/* Step 1: Category Selection */}
      {step === 1 && (
        <div className="animate-fade-in">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {categories.map((cat) => (
              <button
                key={cat.id}
                type="button"
                onClick={(e) => {
                  e.preventDefault()
                  handleCategorySelect(cat.id)
                }}
                className="group relative bg-gradient-to-br from-gray-800 to-gray-900 hover:from-gray-700 hover:to-gray-800 p-8 rounded-2xl text-left transition-all duration-300 hover:scale-105 hover:shadow-2xl border border-gray-700/50 hover:border-gray-600 overflow-hidden"
              >
                {/* Gradient overlay on hover */}
                <div className={`absolute inset-0 bg-gradient-to-br ${cat.gradient} opacity-0 group-hover:opacity-10 transition-opacity duration-300`}></div>

                <div className="relative z-10">
                  <div className="flex items-start justify-between mb-4">
                    <div className="text-6xl transform group-hover:scale-110 transition-transform duration-300">{cat.icon}</div>
                    <svg className="w-6 h-6 text-gray-600 group-hover:text-white transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7"/>
                    </svg>
                  </div>
                  <h3 className="text-2xl font-bold mb-2 group-hover:text-white transition-colors">{cat.name}</h3>
                  <p className="text-gray-400 group-hover:text-gray-300 transition-colors">{cat.description}</p>
                </div>

                {/* Shine effect */}
                <div className="absolute inset-0 -translate-x-full group-hover:translate-x-full transition-transform duration-1000 bg-gradient-to-r from-transparent via-white/5 to-transparent"></div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Step 2: Search */}
      {step === 2 && (
        <div className="animate-fade-in">
          <button
            type="button"
            onClick={(e) => {
              e.preventDefault()
              setStep(1)
            }}
            className="mb-6 text-gray-400 hover:text-white flex items-center gap-2 transition-all group"
          >
            <svg className="w-5 h-5 group-hover:-translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            <span>Back to Categories</span>
          </button>

          <div className="text-center mb-10">
            <div className={`inline-block p-5 rounded-3xl bg-gradient-to-br ${getCategoryInfo()?.gradient} mb-5`}>
              <div className="text-6xl">{getCategoryInfo()?.icon}</div>
            </div>
            <h2 className="text-4xl font-bold mb-3 bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">
              Search {getCategoryInfo()?.name}
            </h2>
            <p className="text-gray-400 text-lg max-w-xl mx-auto">
              {category === 'movies' && "Type a movie name and we'll find similar recommendations"}
              {category === 'tv' && "Type a TV show and we'll find similar series"}
              {category === 'youtube' && "Type what you want to watch"}
              {category === 'tiktok' && "Type viral trends or topics"}
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="relative">
              <div className="absolute inset-y-0 left-4 flex items-center pointer-events-none">
                <svg className="w-6 h-6 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
                </svg>
              </div>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder={getCategoryInfo()?.placeholder}
                className="w-full bg-gradient-to-br from-gray-800 to-gray-900 text-white pl-14 pr-6 py-5 rounded-2xl text-lg focus:outline-none focus:ring-2 focus:ring-primary border border-gray-700 placeholder-gray-500"
                autoFocus
              />
            </div>

            <div className="bg-gradient-to-br from-gray-800 to-gray-900 p-6 rounded-2xl border border-gray-700">
              <label className="flex items-center gap-2 text-sm font-semibold mb-3 text-gray-300">
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd"/>
                </svg>
                Region
              </label>
              <select
                value={region}
                onChange={(e) => setRegion(e.target.value)}
                className="w-full bg-gray-700 text-white px-4 py-3 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary border border-gray-600"
              >
                <option value="US">🇺🇸 United States</option>
                <option value="GB">🇬🇧 United Kingdom</option>
                <option value="CA">🇨🇦 Canada</option>
                <option value="AU">🇦🇺 Australia</option>
                <option value="IN">🇮🇳 India</option>
                <option value="DE">🇩🇪 Germany</option>
                <option value="FR">🇫🇷 France</option>
                <option value="JP">🇯🇵 Japan</option>
              </select>
            </div>

            <button
              type="submit"
              disabled={!searchQuery.trim()}
              className={`w-full py-5 rounded-2xl font-bold text-lg transition-all shadow-lg ${
                searchQuery.trim()
                  ? `bg-gradient-to-r ${getCategoryInfo()?.gradient} hover:shadow-2xl hover:scale-[1.02]`
                  : 'bg-gray-700 text-gray-500 cursor-not-allowed'
              }`}
            >
              {searchQuery.trim() ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z"/>
                  </svg>
                  Get Recommendations
                </span>
              ) : (
                'Enter search query'
              )}
            </button>
          </form>
        </div>
      )}
    </div>
  )
}
