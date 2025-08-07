export type JobStatus = "UPLOADED" | "PENDING" | "READYTOPRINT" | "PRINTING" | "COMPLETED" | "PAIDPICKEDUP" | "REJECTED"

export interface Job {
  id: string
  studentName: string
  studentEmail: string
  discipline: string
  classNumber: string
  originalFilename: string
  displayName: string
  filePath: string
  metadataPath: string
  status: JobStatus
  printer: string | null
  color: string | null
  material: string | null
  weightG: number | null
  timeHours: number | null
  costUsd: number | null
  createdAt: string
  updatedAt: string
  staffViewedAt: string | null
  notes: string | null // Add notes field
}

export interface JobStats {
  uploaded: number
  pending: number
  readyToPrint: number
  printing: number
  completed: number
  paidPickedUp: number
  rejected: number
}
