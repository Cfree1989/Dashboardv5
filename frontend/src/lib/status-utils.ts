/**
 * Status Display Utilities
 * 
 * This module provides consistent status display formatting following the masterplan's
 * three-tier naming convention:
 * 
 * 1. Internal Identifiers: UPPERCASE (e.g., READYTOPRINT, PAIDPICKEDUP)
 * 2. Directory Names: PascalCase (e.g., ReadyToPrint, PaidPickedUp) 
 * 3. User Interface: Title Case with spaces (e.g., "Ready to Print", "Paid & Picked Up")
 */

import { JobStatus } from '../types';

/**
 * Convert internal status identifier to user-friendly display name
 */
export function getStatusDisplayName(status: JobStatus | string): string {
  const statusMap: Record<string, string> = {
    [JobStatus.UPLOADED]: "Uploaded",
    [JobStatus.PENDING]: "Pending", 
    [JobStatus.READYTOPRINT]: "Ready to Print",
    [JobStatus.PRINTING]: "Printing",
    [JobStatus.COMPLETED]: "Completed",
    [JobStatus.PAIDPICKEDUP]: "Paid & Picked Up",
    [JobStatus.REJECTED]: "Rejected",
    [JobStatus.ARCHIVED]: "Archived"
  };
  
  return statusMap[status] || status;
}

/**
 * Convert internal status identifier to directory name (PascalCase)
 */
export function getStatusDirectoryName(status: JobStatus | string): string {
  const directoryMap: Record<string, string> = {
    [JobStatus.UPLOADED]: "Uploaded",
    [JobStatus.PENDING]: "Pending",
    [JobStatus.READYTOPRINT]: "ReadyToPrint", 
    [JobStatus.PRINTING]: "Printing",
    [JobStatus.COMPLETED]: "Completed",
    [JobStatus.PAIDPICKEDUP]: "PaidPickedUp",
    [JobStatus.REJECTED]: "Rejected",
    [JobStatus.ARCHIVED]: "Archived"
  };
  
  return directoryMap[status] || status;
}

/**
 * Get status color class for UI styling
 */
export function getStatusColorClass(status: JobStatus | string): string {
  const colorMap: Record<string, string> = {
    [JobStatus.UPLOADED]: "bg-blue-100 text-blue-800",
    [JobStatus.PENDING]: "bg-yellow-100 text-yellow-800",
    [JobStatus.READYTOPRINT]: "bg-green-100 text-green-800", 
    [JobStatus.PRINTING]: "bg-purple-100 text-purple-800",
    [JobStatus.COMPLETED]: "bg-emerald-100 text-emerald-800",
    [JobStatus.PAIDPICKEDUP]: "bg-gray-100 text-gray-800",
    [JobStatus.REJECTED]: "bg-red-100 text-red-800",
    [JobStatus.ARCHIVED]: "bg-slate-100 text-slate-600"
  };
  
  return colorMap[status] || "bg-gray-100 text-gray-800";
}

/**
 * Get all valid status transitions from a given status
 */
export function getValidStatusTransitions(fromStatus: JobStatus): JobStatus[] {
  const transitionMap: Record<JobStatus, JobStatus[]> = {
    [JobStatus.UPLOADED]: [JobStatus.PENDING, JobStatus.REJECTED, JobStatus.ARCHIVED],
    [JobStatus.PENDING]: [JobStatus.READYTOPRINT, JobStatus.REJECTED],
    [JobStatus.READYTOPRINT]: [JobStatus.PRINTING],
    [JobStatus.PRINTING]: [JobStatus.COMPLETED, JobStatus.READYTOPRINT], 
    [JobStatus.COMPLETED]: [JobStatus.PAIDPICKEDUP, JobStatus.PRINTING],
    [JobStatus.PAIDPICKEDUP]: [JobStatus.COMPLETED],
    [JobStatus.REJECTED]: [],
    [JobStatus.ARCHIVED]: []
  };
  
  return transitionMap[fromStatus] || [];
}

/**
 * Check if a status transition is valid
 */
export function isValidStatusTransition(fromStatus: JobStatus, toStatus: JobStatus): boolean {
  return getValidStatusTransitions(fromStatus).includes(toStatus);
}

/**
 * Get status description for tooltips/help text
 */
export function getStatusDescription(status: JobStatus | string): string {
  const descriptionMap: Record<string, string> = {
    [JobStatus.UPLOADED]: "Job has been submitted but not yet reviewed",
    [JobStatus.PENDING]: "Job is waiting for approval or rejection",
    [JobStatus.READYTOPRINT]: "Job is approved and ready to be printed",
    [JobStatus.PRINTING]: "Job is currently being printed",
    [JobStatus.COMPLETED]: "Job has finished printing and is ready for pickup",
    [JobStatus.PAIDPICKEDUP]: "Job has been paid for and picked up by student",
    [JobStatus.REJECTED]: "Job was rejected and cannot be printed",
    [JobStatus.ARCHIVED]: "Job has been archived for long-term storage"
  };
  
  return descriptionMap[status] || "Unknown status";
}
