import { useDashboard } from "./dashboard-context"
import { Clock } from "lucide-react"

export function LastUpdated() {
  const { lastUpdated } = useDashboard()

  if (!lastUpdated) return null

  const formattedTime = lastUpdated.toLocaleTimeString()

  return (
    <div className="flex items-center text-sm text-gray-500">
      <Clock className="w-4 h-4 mr-1" />
      <span>Last updated: {formattedTime}</span>
    </div>
  )
}
