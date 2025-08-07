"use client"

export function JobCardSkeleton() {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 animate-pulse">
      <div className="p-4">
        {/* Header with title and time */}
        <div className="flex justify-between items-start mb-3">
          <div className="h-5 bg-gray-200 rounded w-32"></div>
          <div className="h-4 bg-gray-200 rounded w-20"></div>
        </div>

        {/* File name */}
        <div className="h-4 bg-gray-200 rounded w-40 mb-3"></div>

        {/* Grid of details */}
        <div className="grid grid-cols-2 gap-2 mb-3">
          <div className="flex items-center space-x-2">
            <div className="h-4 w-4 bg-gray-200 rounded"></div>
            <div className="h-3 bg-gray-200 rounded w-20"></div>
          </div>
          <div className="flex items-center space-x-2">
            <div className="h-4 w-4 bg-gray-200 rounded"></div>
            <div className="h-3 bg-gray-200 rounded w-24"></div>
          </div>
          <div className="flex items-center space-x-2">
            <div className="h-4 w-4 bg-gray-200 rounded"></div>
            <div className="h-3 bg-gray-200 rounded w-16"></div>
          </div>
          <div className="flex items-center space-x-2">
            <div className="h-4 w-4 bg-gray-200 rounded"></div>
            <div className="h-3 bg-gray-200 rounded w-18"></div>
          </div>
        </div>

        {/* Action row */}
        <div className="flex items-center justify-between mt-4">
          <div className="h-4 bg-gray-200 rounded w-20"></div>
          <div className="flex space-x-2">
            <div className="h-8 bg-gray-200 rounded w-20"></div>
            <div className="h-8 bg-gray-200 rounded w-16"></div>
          </div>
        </div>
      </div>
    </div>
  )
}

export function JobListSkeleton() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {Array.from({ length: 6 }).map((_, index) => (
        <JobCardSkeleton key={index} />
      ))}
    </div>
  )
}
