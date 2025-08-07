import type { Job, JobStatus, JobStats } from "@/types/job"

// Mock data for demonstration
const mockJobs: Job[] = [
  {
    id: "1",
    studentName: "Jane Doe",
    studentEmail: "jane.doe@example.edu",
    discipline: "Architecture",
    classNumber: "ARCH 4000",
    originalFilename: "building_model.stl",
    displayName: "JaneDoe_Filament_Blue_123abc.stl",
    filePath: "Z:\\storage\\Uploaded\\JaneDoe_Filament_Blue_123abc.stl",
    metadataPath: "Z:\\storage\\Uploaded\\JaneDoe_Filament_Blue_123abc.json",
    status: "UPLOADED",
    printer: "Prusa MK4S",
    color: "Blue",
    material: "PLA",
    weightG: null,
    timeHours: null,
    costUsd: null,
    createdAt: "2023-09-15T14:30:00Z",
    updatedAt: "2023-09-15T14:30:00Z",
    staffViewedAt: null,
    notes: null,
  },
  {
    id: "2",
    studentName: "John Smith",
    studentEmail: "john.smith@example.edu",
    discipline: "Engineering",
    classNumber: "ENGR 3050",
    originalFilename: "gear_assembly.stl",
    displayName: "JohnSmith_Filament_Red_456def.stl",
    filePath: "Z:\\storage\\Uploaded\\JohnSmith_Filament_Red_456def.stl",
    metadataPath: "Z:\\storage\\Uploaded\\JohnSmith_Filament_Red_456def.json",
    status: "UPLOADED",
    printer: "Prusa XL",
    color: "Red",
    material: "PETG",
    weightG: null,
    timeHours: null,
    costUsd: null,
    createdAt: "2023-09-14T09:15:00Z",
    updatedAt: "2023-09-14T09:15:00Z",
    staffViewedAt: "2023-09-14T10:30:00Z",
    notes: "Student mentioned this is for senior capstone project. May need extra support material.",
  },
  {
    id: "3",
    studentName: "Alice Johnson",
    studentEmail: "alice.johnson@example.edu",
    discipline: "Art",
    classNumber: "ART 2100",
    originalFilename: "sculpture.obj",
    displayName: "AliceJohnson_Resin_Clear_789ghi.obj",
    filePath: "Z:\\storage\\Pending\\AliceJohnson_Resin_Clear_789ghi.obj",
    metadataPath: "Z:\\storage\\Pending\\AliceJohnson_Resin_Clear_789ghi.json",
    status: "PENDING",
    printer: "Formlabs Form 3",
    color: "Clear",
    material: "Standard Resin",
    weightG: 45.2,
    timeHours: 3.5,
    costUsd: 9.04,
    createdAt: "2023-09-13T16:45:00Z",
    updatedAt: "2023-09-13T17:30:00Z",
    staffViewedAt: "2023-09-13T17:00:00Z",
    notes: "Requires careful handling - delicate features. Print at 0.05mm layer height.",
  },
]

// Mock stats
const mockStats: JobStats = {
  uploaded: 2,
  pending: 1,
  readyToPrint: 0,
  printing: 0,
  completed: 0,
  paidPickedUp: 0,
  rejected: 0,
}

// In a real implementation, these would make actual API calls
export async function fetchJobs(status: JobStatus = "UPLOADED"): Promise<Job[]> {
  // Simulate API call delay
  await new Promise((resolve) => setTimeout(resolve, 500))

  // Filter jobs by status
  return mockJobs.filter((job) => job.status === status)
}

export async function fetchJobStats(): Promise<JobStats> {
  // Simulate API call delay
  await new Promise((resolve) => setTimeout(resolve, 300))

  return mockStats
}

export async function fetchJobById(id: string): Promise<Job | null> {
  // Simulate API call delay
  await new Promise((resolve) => setTimeout(resolve, 200))

  return mockJobs.find((job) => job.id === id) || null
}

// Add function to update job notes
export async function updateJobNotes(jobId: string, notes: string): Promise<boolean> {
  // Simulate API call delay
  await new Promise((resolve) => setTimeout(resolve, 300))

  // In a real implementation, this would make an API call to update the job
  const jobIndex = mockJobs.findIndex((job) => job.id === jobId)
  if (jobIndex !== -1) {
    mockJobs[jobIndex].notes = notes
    mockJobs[jobIndex].updatedAt = new Date().toISOString()
    return true
  }
  return false
}
