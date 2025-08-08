export interface StaffMember {
  id: string
  name: string
  email: string
  isActive: boolean
  createdAt: string
  lastLogin: string | null
}

export interface SystemInfo {
  version: string
  environment: string
  uptime: string
  storageUsed: number
  storageLimit: number
}

export interface AuditReport {
  id: string
  startedAt: string
  completedAt: string | null
  status: "running" | "completed" | "failed"
  orphanedFiles: number
  brokenFiles: number
  staleFiles: number
  totalScanned: number
}

export interface AdminOverride {
  jobId: string
  action: "unlock" | "confirm" | "change_status" | "mark_failed"
  reason: string
  newStatus?: string
}

export interface ArchiveOptions {
  retentionDays: number
  previewCount: number
}

export interface PruneOptions {
  olderThanDays: number
  previewCount: number
}
