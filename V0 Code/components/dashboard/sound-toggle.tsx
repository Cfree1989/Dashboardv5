"use client"

import { Volume2, VolumeX, TestTube } from "lucide-react"
import { useDashboard } from "./dashboard-context"
import { useState } from "react"

export function SoundToggle() {
  const { soundEnabled, toggleSound, testSound } = useDashboard()
  const [isToggling, setIsToggling] = useState(false)

  const handleToggle = async () => {
    setIsToggling(true)
    await toggleSound()
    // Add a small delay to show the toggling state
    setTimeout(() => {
      setIsToggling(false)
    }, 500)
  }

  return (
    <div className="flex items-center space-x-2">
      <button
        onClick={handleToggle}
        disabled={isToggling}
        className={`
          flex items-center px-3 py-2 rounded-lg border transition-all duration-200
          ${isToggling ? "opacity-50 cursor-not-allowed" : ""}
          ${soundEnabled ? "bg-blue-100 text-blue-700 border-blue-200" : "bg-gray-100 text-gray-500 border-gray-200"}
        `}
        title={soundEnabled ? "Disable sound notifications" : "Enable sound notifications"}
      >
        {soundEnabled ? (
          <>
            <Volume2 className="w-4 h-4 mr-2" />
            <span className="text-sm">{isToggling ? "Enabling..." : "Sound On"}</span>
          </>
        ) : (
          <>
            <VolumeX className="w-4 h-4 mr-2" />
            <span className="text-sm">{isToggling ? "Disabling..." : "Sound Off"}</span>
          </>
        )}
      </button>

      {soundEnabled && !isToggling && (
        <button
          onClick={testSound}
          className="flex items-center px-2 py-2 rounded-lg border border-blue-200 bg-blue-50 text-blue-600 hover:bg-blue-100 transition-colors"
          title="Test notification sound"
        >
          <TestTube className="w-4 h-4" />
        </button>
      )}
    </div>
  )
}
