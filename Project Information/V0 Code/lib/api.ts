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
  {
    id: "4",
    studentName: "Mike Chen",
    studentEmail: "mike.chen@example.edu",
    discipline: "Design",
    classNumber: "DSGN 2500",
    originalFilename: "prototype_v2.stl",
    displayName: "MikeChen_Filament_Black_101xyz.stl",
    filePath: "Z:\\storage\\ReadyToPrint\\MikeChen_Filament_Black_101xyz.stl",
    metadataPath: "Z:\\storage\\ReadyToPrint\\MikeChen_Filament_Black_101xyz.json",
    status: "READYTOPRINT",
    printer: "Prusa MK4S",
    color: "Black",
    material: "PLA",
    weightG: 28.7,
    timeHours: 2.25,
    costUsd: 5.74,
    createdAt: "2023-09-12T11:20:00Z",
    updatedAt: "2023-09-15T09:45:00Z",
    staffViewedAt: "2023-09-12T14:30:00Z",
    notes: "Ready for printing. Student requested black PLA specifically for this prototype.",
  },
  {
    id: "5",
    studentName: "Sarah Wilson",
    studentEmail: "sarah.wilson@example.edu",
    discipline: "Engineering",
    classNumber: "MECH 4100",
    originalFilename: "bearing_housing.stl",
    displayName: "SarahWilson_Filament_Gray_202abc.stl",
    filePath: "Z:\\storage\\Printing\\SarahWilson_Filament_Gray_202abc.stl",
    metadataPath: "Z:\\storage\\Printing\\SarahWilson_Filament_Gray_202abc.json",
    status: "PRINTING",
    printer: "Prusa XL",
    color: "Gray",
    material: "PETG",
    weightG: 67.3,
    timeHours: 4.75,
    costUsd: 13.46,
    createdAt: "2023-09-11T08:30:00Z",
    updatedAt: "2023-09-15T13:20:00Z",
    staffViewedAt: "2023-09-11T10:15:00Z",
    notes: "Currently printing on Prusa XL. Estimated completion: 6:30 PM today.",
  },
  {
    id: "6",
    studentName: "David Brown",
    studentEmail: "david.brown@example.edu",
    discipline: "Architecture",
    classNumber: "ARCH 3200",
    originalFilename: "building_section.stl",
    displayName: "DavidBrown_Filament_White_303def.stl",
    filePath: "Z:\\storage\\Completed\\DavidBrown_Filament_White_303def.stl",
    metadataPath: "Z:\\storage\\Completed\\DavidBrown_Filament_White_303def.json",
    status: "COMPLETED",
    printer: "Prusa MK4S",
    color: "White",
    material: "PLA",
    weightG: 52.1,
    timeHours: 3.8,
    costUsd: 10.42,
    createdAt: "2023-09-10T14:15:00Z",
    updatedAt: "2023-09-15T11:45:00Z",
    staffViewedAt: "2023-09-10T16:20:00Z",
    notes: "Print completed successfully. Ready for student pickup.",
  },
  {
    id: "7",
    studentName: "Emma Davis",
    studentEmail: "emma.davis@example.edu",
    discipline: "Art",
    classNumber: "ARTS 1800",
    originalFilename: "artistic_piece.obj",
    displayName: "EmmaDavis_Resin_Transparent_404ghi.obj",
    filePath: "Z:\\storage\\PaidPickedUp\\EmmaDavis_Resin_Transparent_404ghi.obj",
    metadataPath: "Z:\\storage\\PaidPickedUp\\EmmaDavis_Resin_Transparent_404ghi.json",
    status: "PAIDPICKEDUP",
    printer: "Formlabs Form 3",
    color: "Transparent",
    material: "Clear Resin",
    weightG: 31.8,
    timeHours: 2.5,
    costUsd: 6.36,
    createdAt: "2023-09-08T13:45:00Z",
    updatedAt: "2023-09-14T16:30:00Z",
    staffViewedAt: "2023-09-08T15:10:00Z",
    notes: "Student paid and picked up on 9/14. Beautiful transparent finish achieved.",
  },
  {
    id: "8",
    studentName: "Tom Garcia",
    studentEmail: "tom.garcia@example.edu",
    discipline: "Engineering",
    classNumber: "ENGR 2800",
    originalFilename: "faulty_design.stl",
    displayName: "TomGarcia_Filament_Blue_505jkl.stl",
    filePath: "Z:\\storage\\Rejected\\TomGarcia_Filament_Blue_505jkl.stl",
    metadataPath: "Z:\\storage\\Rejected\\TomGarcia_Filament_Blue_505jkl.json",
    status: "REJECTED",
    printer: null,
    color: "Blue",
    material: "PLA",
    weightG: null,
    timeHours: null,
    costUsd: null,
    createdAt: "2023-09-13T10:20:00Z",
    updatedAt: "2023-09-14T14:15:00Z",
    staffViewedAt: "2023-09-13T11:45:00Z",
    notes: "Rejected due to non-manifold mesh. Student notified to fix geometry and resubmit.",
  },
]

// Mock stats
const mockStats: JobStats = {
  uploaded: 2,
  pending: 1,
  readyToPrint: 1,
  printing: 1,
  completed: 1,
  paidPickedUp: 1,
  rejected: 1,
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
