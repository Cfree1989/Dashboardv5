"use client"

import { useState } from "react"
import { formatDistanceToNow } from "date-fns"
import type { Job, JobStatus } from "@/types/job"
import { useDashboard } from "./dashboard-context"
import { NotesSection } from "./notes-section"
import { User, Mail, Printer, Palette, DollarSign, CheckCircle, XCircle, ExternalLink, Eye } from "lucide-react"

interface JobCardProps {
  job: Job
  currentStatus: JobStatus
  onApprove: (jobId: string) => void
  onReject: (jobId: string) => void
}

export function JobCard({ job, currentStatus, onApprove, onReject }: JobCardProps) {
  const { markJobAsReviewed } = useDashboard()
  const [isExpanded, setIsExpanded] = useState(false)

  const isUnreviewed = !job.staffViewedAt

  // Calculate job age and determine color
  const getAgeColor = (createdAt: string) => {
    const ageInHours = (Date.now() - new Date(createdAt).getTime()) / (1000 * 60 * 60)

    if (ageInHours < 24) return "text-green-600"
    if (ageInHours < 48) return "text-yellow-600"
    if (ageInHours < 72) return "text-orange-600"
    return "text-red-600"
  }

  const ageColor = getAgeColor(job.createdAt)

  // Format time elapsed
  const timeElapsed = formatDistanceToNow(new Date(job.createdAt), { addSuffix: true })

  return (
    <div
      className={`
      bg-white rounded-xl shadow-sm border transition-all
      ${isUnreviewed ? "border-orange-400 shadow-orange-100 animate-pulse-subtle" : "border-gray-200"}
    `}
    >
      <div className="p-4">
        {isUnreviewed && (
          <div className="flex items-center justify-between mb-3">
            <span className="bg-orange-100 text-orange-800 text-xs font-semibold px-2 py-1 rounded-full">NEW</span>
            <button
              onClick={() => markJobAsReviewed(job.id)}
              className="text-xs text-gray-500 hover:text-gray-700 flex items-center"
            >
              <Eye className="w-3 h-3 mr-1" />
              Mark as Reviewed
            </button>
          </div>
        )}

        <div className="flex justify-between items-start mb-3">
          <h3 className="text-lg font-semibold text-gray-900 truncate">{job.studentName}</h3>
          <span className={`text-sm ${ageColor} font-medium`}>{timeElapsed}</span>
        </div>

        <p className="text-gray-600 text-sm mb-3 truncate">{job.displayName}</p>

        <div className="grid grid-cols-2 gap-2 mb-3">
          <div className="flex items-center text-sm text-gray-500">
            <User className="w-4 h-4 mr-1" />
            <span className="truncate">{job.studentName}</span>
          </div>
          <div className="flex items-center text-sm text-gray-500">
            <Mail className="w-4 h-4 mr-1" />
            <span className="truncate">{job.studentEmail}</span>
          </div>
          <div className="flex items-center text-sm text-gray-500">
            <Printer className="w-4 h-4 mr-1" />
            <span className="truncate">{job.printer || "Not set"}</span>
          </div>
          <div className="flex items-center text-sm text-gray-500">
            <Palette className="w-4 h-4 mr-1" />
            <span className="truncate">{job.color || "Not set"}</span>
          </div>
        </div>

        {job.costUsd && (
          <div className="flex items-center text-sm font-medium text-gray-900 mb-3">
            <DollarSign className="w-4 h-4 mr-1" />${job.costUsd.toFixed(2)}
          </div>
        )}

        {/* Notes section - always show when collapsed if there are notes */}
        <NotesSection jobId={job.id} notes={job.notes} isExpanded={isExpanded} />

        {isExpanded && (
          <div className="mt-3 pt-3 border-t border-gray-100">
            <h4 className="text-sm font-medium text-gray-900 mb-2">Additional Details</h4>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div>
                <span className="text-gray-500">Discipline:</span>
                <p className="text-gray-900">{job.discipline}</p>
              </div>
              <div>
                <span className="text-gray-500">Class:</span>
                <p className="text-gray-900">{job.classNumber}</p>
              </div>
              <div>
                <span className="text-gray-500">Material:</span>
                <p className="text-gray-900">{job.material || "Not set"}</p>
              </div>
              <div>
                <span className="text-gray-500">Weight:</span>
                <p className="text-gray-900">{job.weightG ? `${job.weightG}g` : "Not set"}</p>
              </div>
              <div>
                <span className="text-gray-500">Time:</span>
                <p className="text-gray-900">{job.timeHours ? `${job.timeHours}h` : "Not set"}</p>
              </div>
              <div>
                <span className="text-gray-500">Created:</span>
                <p className="text-gray-900">{new Date(job.createdAt).toLocaleString()}</p>
              </div>
            </div>
          </div>
        )}

        <div className="flex items-center justify-between mt-4">
          <button onClick={() => setIsExpanded(!isExpanded)} className="text-sm text-gray-500 hover:text-gray-700">
            {isExpanded ? "Show Less" : "Show More"}
          </button>

          <div className="flex space-x-2">
            {currentStatus === "UPLOADED" && (
              <>
                <button
                  onClick={() => onApprove(job.id)}
                  className="flex items-center px-3 py-1 bg-green-100 text-green-700 rounded-lg hover:bg-green-200"
                >
                  <CheckCircle className="w-4 h-4 mr-1" />
                  Approve
                </button>
                <button
                  onClick={() => onReject(job.id)}
                  className="flex items-center px-3 py-1 bg-red-100 text-red-700 rounded-lg hover:bg-red-200"
                >
                  <XCircle className="w-4 h-4 mr-1" />
                  Reject
                </button>
              </>
            )}

            {(currentStatus === "READYTOPRINT" || currentStatus === "PRINTING") && (
              <a
                href={`3dprint://open?path=${encodeURIComponent(job.filePath)}`}
                className="flex items-center px-3 py-1 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200"
              >
                <ExternalLink className="w-4 h-4 mr-1" />
                Open File
              </a>
            )}

            {currentStatus === "READYTOPRINT" && (
              <button className="flex items-center px-3 py-1 bg-purple-100 text-purple-700 rounded-lg hover:bg-purple-200">
                <Printer className="w-4 h-4 mr-1" />
                Mark Printing
              </button>
            )}

            {currentStatus === "PRINTING" && (
              <button className="flex items-center px-3 py-1 bg-green-100 text-green-700 rounded-lg hover:bg-green-200">
                <CheckCircle className="w-4 h-4 mr-1" />
                Mark Complete
              </button>
            )}

            {currentStatus === "COMPLETED" && (
              <button className="flex items-center px-3 py-1 bg-green-100 text-green-700 rounded-lg hover:bg-green-200">
                <DollarSign className="w-4 h-4 mr-1" />
                Mark Paid/Picked Up
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
