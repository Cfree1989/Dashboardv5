"use client"

import { JobStatus } from '../../types';

interface StatusTabsProps {
  currentStatus: string
  onStatusChange: (status: string) => void
  stats: Record<string, number>
  matchCounts?: Record<string, number>
  searchActive?: boolean
}

interface TabConfig {
  key: JobStatus
  title: string
}

export function StatusTabs({ currentStatus, onStatusChange, stats, matchCounts, searchActive }: StatusTabsProps) {
  const tabs: TabConfig[] = [
    { key: JobStatus.UPLOADED, title: "Uploaded" },
    { key: JobStatus.PENDING, title: "Pending" },
    { key: JobStatus.READYTOPRINT, title: "Ready to Print" },
    { key: JobStatus.PRINTING, title: "Printing" },
    { key: JobStatus.COMPLETED, title: "Completed" },
    { key: JobStatus.PAIDPICKEDUP, title: "Paid & Picked Up" },
    { key: JobStatus.REJECTED, title: "Rejected" },
    { key: JobStatus.ARCHIVED, title: "Archived" },
  ]

  return (
    <div className="flex space-x-1 mb-6 overflow-x-auto pb-2">
      {tabs.map((tab) => (
        <button
          key={tab.key}
          onClick={() => onStatusChange(tab.key)}
          className={`
            flex items-center justify-between px-4 py-3 rounded-xl border 
            transition-all duration-200 whitespace-nowrap flex-shrink-0 min-w-fit
            ${
              currentStatus === tab.key
                ? "bg-blue-600 text-white shadow-md border-blue-600"
                : "bg-white text-blue-600 border-gray-200 hover:bg-blue-50 hover:shadow-sm"
            }
          `}
        >
          <span className="font-medium">{tab.title}</span>
          <span
            className={`
            ml-2 px-2 py-1 text-xs font-semibold rounded-full
            ${currentStatus === tab.key ? (searchActive ? "bg-orange-500 text-white" : "bg-blue-500 text-white") : (searchActive ? "bg-orange-100 text-orange-800" : "bg-blue-100 text-blue-800")}
          `}
          >
            {searchActive && matchCounts ? (matchCounts[tab.key] || 0) : (stats[tab.key] || 0)}
          </span>
        </button>
      ))}
    </div>
  )
}
