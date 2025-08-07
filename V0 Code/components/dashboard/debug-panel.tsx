"use client"

import { useDashboard } from "./dashboard-context"
import { useState } from "react"

export function DebugPanel() {
  const { soundEnabled, stats } = useDashboard()
  const [isVisible, setIsVisible] = useState(false)

  if (!isVisible) {
    return (
      <button
        onClick={() => setIsVisible(true)}
        className="fixed bottom-4 right-4 px-2 py-1 bg-gray-800 text-white text-xs rounded"
      >
        Debug
      </button>
    )
  }

  return (
    <div className="fixed bottom-4 right-4 bg-gray-800 text-white p-4 rounded-lg text-xs max-w-xs">
      <div className="flex justify-between items-center mb-2">
        <h3 className="font-bold">Debug Info</h3>
        <button onClick={() => setIsVisible(false)} className="text-gray-400 hover:text-white">
          ×
        </button>
      </div>
      <div className="space-y-1">
        <div>Sound Enabled: {soundEnabled ? "Yes" : "No"}</div>
        <div>Uploaded Jobs: {stats.uploaded}</div>
        <div>Pending Jobs: {stats.pending}</div>
        <div>Ready to Print: {stats.readyToPrint}</div>
        <div>Browser: {typeof window !== "undefined" ? "Client" : "Server"}</div>
        <div>Audio Support: {typeof Audio !== "undefined" ? "Yes" : "No"}</div>
        <div>LocalStorage: {typeof localStorage !== "undefined" ? "Available" : "Not Available"}</div>
        <div className="pt-2 border-t border-gray-600">
          <div className="text-gray-300">Sound will only play when:</div>
          <div>• Sound is enabled</div>
          <div>• Not initial page load</div>
          <div>• Upload count increases</div>
        </div>
      </div>
    </div>
  )
}
