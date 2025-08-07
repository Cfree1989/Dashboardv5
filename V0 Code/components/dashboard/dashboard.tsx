"use client"

import { useState } from "react"
import { StatusTabs } from "./status-tabs"
import { JobList } from "./job-list"
import { SoundToggle } from "./sound-toggle"
import { LastUpdated } from "./last-updated"
import { DebugPanel } from "./debug-panel"
import { useDashboard } from "./dashboard-context"
import type { JobStatus } from "@/types/job"
import { ApprovalModal } from "./modals/approval-modal"
import { RejectionModal } from "./modals/rejection-modal"

interface DashboardProps {
  currentStatus: JobStatus
  onStatusChange: (status: JobStatus) => void
}

export function Dashboard({ currentStatus, onStatusChange }: DashboardProps) {
  const { jobs, stats, loading, refreshData } = useDashboard()
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null)
  const [isApprovalModalOpen, setIsApprovalModalOpen] = useState(false)
  const [isRejectionModalOpen, setIsRejectionModalOpen] = useState(false)

  const handleStatusChange = (status: JobStatus) => {
    onStatusChange(status)
    refreshData(status)
  }

  const handleApproveClick = (jobId: string) => {
    setSelectedJobId(jobId)
    setIsApprovalModalOpen(true)
  }

  const handleRejectClick = (jobId: string) => {
    setSelectedJobId(jobId)
    setIsRejectionModalOpen(true)
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex flex-col md:flex-row md:items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-4 md:mb-0">3D Print Job Dashboard</h1>
        <div className="flex items-center space-x-4">
          <SoundToggle />
          <LastUpdated />
          <button
            onClick={() => refreshData(currentStatus)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
            disabled={loading}
          >
            {loading ? "Refreshing..." : "Refresh"}
          </button>
        </div>
      </div>

      <StatusTabs currentStatus={currentStatus} onStatusChange={handleStatusChange} stats={stats} />

      <JobList jobs={jobs} currentStatus={currentStatus} onApprove={handleApproveClick} onReject={handleRejectClick} />

      {selectedJobId && (
        <>
          <ApprovalModal
            isOpen={isApprovalModalOpen}
            onClose={() => setIsApprovalModalOpen(false)}
            jobId={selectedJobId}
          />
          <RejectionModal
            isOpen={isRejectionModalOpen}
            onClose={() => setIsRejectionModalOpen(false)}
            jobId={selectedJobId}
          />
        </>
      )}

      <DebugPanel />
    </div>
  )
}
