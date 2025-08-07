"use client"

interface StatusTabsProps {
  currentStatus: string
  onStatusChange: (status: string) => void
  stats: Record<string, number>
}

interface TabConfig {
  key: string
  title: string
}

export function StatusTabs({ currentStatus, onStatusChange, stats }: StatusTabsProps) {
  const tabs: TabConfig[] = [
    { key: "UPLOADED", title: "Uploaded" },
    { key: "PENDING", title: "Pending" },
    { key: "READYTOPRINT", title: "Ready to Print" },
    { key: "PRINTING", title: "Printing" },
    { key: "COMPLETED", title: "Completed" },
    { key: "PAIDPICKEDUP", title: "Picked Up" },
    { key: "ARCHIVED", title: "Archived" },
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
            ${currentStatus === tab.key ? "bg-blue-500 text-white" : "bg-blue-100 text-blue-800"}
          `}
          >
            {stats[tab.key] || 0}
          </span>
        </button>
      ))}
    </div>
  )
}
