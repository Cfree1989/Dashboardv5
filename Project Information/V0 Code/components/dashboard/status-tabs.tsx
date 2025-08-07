"use client"

import type { JobStatus, JobStats } from "@/types/job"

interface StatusTabsProps {
  currentStatus: JobStatus
  onStatusChange: (status: JobStatus) => void
  stats: JobStats
}

interface TabConfig {
  key: JobStatus
  title: string
  statKey: keyof JobStats
}

export function StatusTabs({ currentStatus, onStatusChange, stats }: StatusTabsProps) {
  const tabs: TabConfig[] = [
    { key: "UPLOADED", title: "Uploaded", statKey: "uploaded" },
    { key: "PENDING", title: "Pending", statKey: "pending" },
    { key: "READYTOPRINT", title: "Ready to Print", statKey: "readyToPrint" },
    { key: "PRINTING", title: "Printing", statKey: "printing" },
    { key: "COMPLETED", title: "Completed", statKey: "completed" },
    { key: "PAIDPICKEDUP", title: "Picked Up", statKey: "paidPickedUp" },
    { key: "REJECTED", title: "Rejected", statKey: "rejected" },
  ]

  return (
    <div className="flex space-x-1 mb-6 overflow-x-auto pb-2">
      {tabs.map((tab) => (
        <button
          key={tab.key}
          onClick={() => onStatusChange(tab.key)}
          className={`
            flex items-center justify-between px-4 py-3 rounded-xl border 
            transition-all duration-200 whitespace-nowrap flex-shrink-0
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
            ${currentStatus === tab.key ? "bg-blue-500 text-white" : "bg-blue-100 text-blue-800"}
          `}
          >
            {stats[tab.statKey]}
          </span>
        </button>
      ))}
    </div>
  )
}
