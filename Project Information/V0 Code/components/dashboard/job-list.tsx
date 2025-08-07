import type { Job, JobStatus } from "@/types/job"
import { JobCard } from "./job-card"

interface JobListProps {
  jobs: Job[]
  currentStatus: JobStatus
  onApprove: (jobId: string) => void
  onReject: (jobId: string) => void
}

export function JobList({ jobs, currentStatus, onApprove, onReject }: JobListProps) {
  if (jobs.length === 0) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center">
        <p className="text-gray-500">No jobs in this status.</p>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {jobs.map((job) => (
        <JobCard key={job.id} job={job} currentStatus={currentStatus} onApprove={onApprove} onReject={onReject} />
      ))}
    </div>
  )
}
