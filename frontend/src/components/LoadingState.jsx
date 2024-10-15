export default function LoadingState() {
  return (
    <div className="py-20">
      {/* Centered Spinner */}
      <div className="flex flex-col items-center justify-center mb-12">
        <div className="relative">
          {/* Outer ring */}
          <div className="w-24 h-24 rounded-full border-4 border-gray-700"></div>
          {/* Spinning gradient ring */}
          <div className="absolute inset-0 w-24 h-24 rounded-full border-4 border-transparent border-t-primary border-r-pink-500 animate-spin"></div>
          {/* Inner pulsing circle */}
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-12 h-12 bg-gradient-to-br from-primary to-pink-500 rounded-full animate-pulse"></div>
          </div>
        </div>

        <div className="mt-8 text-center">
          <h3 className="text-2xl font-bold mb-2 bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">
            Finding recommendations
          </h3>
          <p className="text-gray-400 animate-pulse">Searching across all streaming platforms...</p>
        </div>
      </div>

      {/* Skeleton Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
          <div
            key={i}
            className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-2xl overflow-hidden animate-pulse border border-gray-700"
            style={{ animationDelay: `${i * 100}ms` }}
          >
            <div className="h-56 bg-gray-700 relative overflow-hidden">
              <div className="absolute inset-0 -translate-x-full animate-shimmer bg-gradient-to-r from-transparent via-gray-600/50 to-transparent"></div>
            </div>
            <div className="p-4 space-y-3">
              <div className="h-5 bg-gray-700 rounded-lg w-3/4"></div>
              <div className="h-4 bg-gray-700 rounded-lg w-full"></div>
              <div className="h-3 bg-gray-700 rounded-lg w-1/2"></div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
