"use client"

import { createContext, useContext, useState, useEffect, useCallback, useRef, type ReactNode } from "react"
import type { Job, JobStatus, JobStats } from "@/types/job"
import { fetchJobs, fetchJobStats, updateJobNotes } from "@/lib/api"

type DashboardContextType = {
  jobs: Job[]
  stats: JobStats
  loading: boolean
  lastUpdated: Date | null
  soundEnabled: boolean
  toggleSound: () => void
  markJobAsReviewed: (jobId: string) => void
  refreshData: () => Promise<void>
  testSound: () => void
  updateNotes: (jobId: string, notes: string) => Promise<boolean>
}

const DashboardContext = createContext<DashboardContextType | undefined>(undefined)

export function DashboardProvider({ children }: { children: ReactNode }) {
  const [jobs, setJobs] = useState<Job[]>([])
  const [stats, setStats] = useState<JobStats>({
    uploaded: 0,
    pending: 0,
    readyToPrint: 0,
    printing: 0,
    completed: 0,
    paidPickedUp: 0,
    rejected: 0,
  })
  const [loading, setLoading] = useState(false)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)
  const [soundEnabled, setSoundEnabled] = useState(false)
  const [isClient, setIsClient] = useState(false)

  // Use refs to track previous stats and whether this is the initial load
  const prevStatsRef = useRef<JobStats | null>(null)
  const isInitialLoadRef = useRef(true)

  // Initialize client-side state
  useEffect(() => {
    setIsClient(true)
    // Load sound preference from localStorage
    const saved = localStorage.getItem("soundEnabled")
    setSoundEnabled(saved === "true")
  }, [])

  // Save sound preference to localStorage whenever it changes
  useEffect(() => {
    if (isClient) {
      localStorage.setItem("soundEnabled", String(soundEnabled))
    }
  }, [soundEnabled, isClient])

  const playNotificationSound = useCallback(async () => {
    if (!isClient) return

    try {
      // Create a new audio instance each time to avoid state issues
      const audio = new Audio("https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3")
      audio.volume = 0.5 // Set volume to 50%

      // Handle the promise returned by play()
      const playPromise = audio.play()

      if (playPromise !== undefined) {
        await playPromise
        console.log("Notification sound played successfully")
      }
    } catch (error) {
      console.log("Could not play notification sound:", error)

      // Try fallback format
      try {
        const fallbackAudio = new Audio("/sounds/notification.wav")
        fallbackAudio.volume = 0.5
        await fallbackAudio.play()
        console.log("Fallback notification sound played successfully")
      } catch (fallbackError) {
        console.log("Could not play fallback sound:", fallbackError)
      }
    }
  }, [isClient])

  const testSound = useCallback(() => {
    if (!isClient) return

    console.log("Testing sound - soundEnabled:", soundEnabled)
    playNotificationSound()
  }, [isClient, soundEnabled, playNotificationSound])

  const toggleSound = useCallback(async () => {
    if (!isClient) return

    const newValue = !soundEnabled
    console.log("Toggling sound from", soundEnabled, "to", newValue)

    // Update the state first
    setSoundEnabled(newValue)

    // If enabling sound, play a test sound after a short delay
    if (newValue) {
      // Use setTimeout to ensure the state update has been processed
      setTimeout(async () => {
        console.log("Playing test sound after enabling")
        await playNotificationSound()
      }, 200)
    }
  }, [isClient, soundEnabled, playNotificationSound])

  const updateNotes = useCallback(async (jobId: string, notes: string): Promise<boolean> => {
    try {
      const success = await updateJobNotes(jobId, notes)
      if (success) {
        // Update local state
        setJobs((prevJobs) =>
          prevJobs.map((job) => (job.id === jobId ? { ...job, notes, updatedAt: new Date().toISOString() } : job)),
        )
      }
      return success
    } catch (error) {
      console.error("Error updating job notes:", error)
      return false
    }
  }, [])

  const refreshData = async (status: JobStatus = "UPLOADED") => {
    try {
      setLoading(true)

      // Fetch new data
      const [newJobs, newStats] = await Promise.all([fetchJobs(status), fetchJobStats()])

      setJobs(newJobs)
      setStats(newStats)
      setLastUpdated(new Date())

      // Only check for new uploads if this is NOT the initial load and we have previous stats
      if (!isInitialLoadRef.current && prevStatsRef.current && soundEnabled) {
        const prevUploadedCount = prevStatsRef.current.uploaded
        const newUploadedCount = newStats.uploaded

        console.log("Checking for new uploads:", {
          previous: prevUploadedCount,
          current: newUploadedCount,
          isInitialLoad: isInitialLoadRef.current,
          soundEnabled,
        })

        // Play sound only if there are actually more uploaded jobs than before
        if (newUploadedCount > prevUploadedCount) {
          console.log("New jobs detected! Playing notification sound")
          await playNotificationSound()
        }
      }

      // Update the previous stats reference
      prevStatsRef.current = { ...newStats }

      // Mark that initial load is complete
      if (isInitialLoadRef.current) {
        isInitialLoadRef.current = false
        console.log("Initial load completed, future refreshes will check for new uploads")
      }
    } catch (error) {
      console.error("Error refreshing data:", error)
    } finally {
      setLoading(false)
    }
  }

  const markJobAsReviewed = async (jobId: string) => {
    try {
      // In a real implementation, this would make an API call
      // await markJobReviewed(jobId)

      // Update local state to reflect the change
      setJobs(jobs.map((job) => (job.id === jobId ? { ...job, staffViewedAt: new Date().toISOString() } : job)))
    } catch (error) {
      console.error("Error marking job as reviewed:", error)
    }
  }

  // Auto-refresh data every 45 seconds
  useEffect(() => {
    if (!isClient) return

    // Initial load
    refreshData()

    const interval = setInterval(() => {
      refreshData()
    }, 45000)

    return () => clearInterval(interval)
  }, [isClient]) // Remove soundEnabled from dependencies since we handle it inside refreshData

  return (
    <DashboardContext.Provider
      value={{
        jobs,
        stats,
        loading,
        lastUpdated,
        soundEnabled,
        toggleSound,
        markJobAsReviewed,
        refreshData,
        testSound,
        updateNotes,
      }}
    >
      {children}
    </DashboardContext.Provider>
  )
}

export function useDashboard() {
  const context = useContext(DashboardContext)
  if (context === undefined) {
    throw new Error("useDashboard must be used within a DashboardProvider")
  }
  return context
}
