"use client"

import { Clock } from "lucide-react"

interface LastUpdatedProps {
  lastUpdated: string | null
}

export function LastUpdated({ lastUpdated }: LastUpdatedProps) {
  if (!lastUpdated) return null

  return (
    <div className="flex items-center text-sm text-gray-500">
      <Clock className="w-4 h-4 mr-1" />
      <span>Last updated: {lastUpdated}</span>
    </div>
  )
}
