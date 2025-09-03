"use client";
import React, { useState } from 'react';
import { 
  CheckCircle, 
  XCircle, 
  ExternalLink, 
  Copy, 
  Archive, 
  Mail,
  Printer
} from "lucide-react";
import { useToast } from "../ui/toast";
import { apiClient } from '../../lib/unified-api-client';
import { Job, JobStatus } from '../../types';

interface Staff {
  name: string;
  is_active: boolean;
}

interface JobCardActionsProps {
  job: Job;
  currentStatus: JobStatus | string;
  isApproving: boolean;
  isRejecting: boolean;
  isDeleting: boolean;
  staff: Staff[];
  loadingStaff: boolean;
  onApprove: () => void;
  onReject: () => void;
  onStatusChange: (config: { action: string; title: string; description: string; confirmVerb: string }) => void;
  onPayment: () => void;
  onDelete: () => void;
  onOpenFile: () => void;
}

/**
 * Convert database file paths to Windows paths for SlicerOpener
 * Handles: /app/storage/... -> C:\Dashboardv5\storage\...
 *         storage/... -> C:\Dashboardv5\storage\...
 *         C:\Dashboardv5\storage\... -> unchanged
 */
function convertToWindowsPath(filePath: string): string {
  if (!filePath) return '';
  
  // Already a Windows path
  if (filePath.startsWith('C:\\Dashboardv5\\storage\\')) {
    return filePath;
  }
  
  // Container absolute path: /app/storage/... -> C:\Dashboardv5\storage\...
  if (filePath.startsWith('/app/storage/')) {
    return filePath.replace('/app/storage/', 'C:\\Dashboardv5\\storage\\').replace(/\//g, '\\');
  }
  
  // Relative path: storage/... -> C:\Dashboardv5\storage\...
  if (filePath.startsWith('storage/')) {
    return `C:\\Dashboardv5\\${filePath}`.replace(/\//g, '\\');
  }
  
  // Fallback: assume relative and prepend base
  return `C:\\Dashboardv5\\storage\\${filePath}`.replace(/\//g, '\\');
}

export function JobCardActions({ 
  job, 
  currentStatus,
  isApproving,
  isRejecting, 
  isDeleting,
  staff,
  loadingStaff,
  onApprove, 
  onReject,
  onStatusChange,
  onPayment,
  onDelete,
  onOpenFile
}: JobCardActionsProps) {
  const { show } = useToast();
  const [showResendModal, setShowResendModal] = useState(false);
  const [resendStaffName, setResendStaffName] = useState("");
  const [isResendingConfirm, setIsResendingConfirm] = useState(false);

  const copyFilePath = async () => {
    // Log the action regardless
    try {
      await apiClient.post(`/api/v1/jobs/${job.id}/log-file-open`, {});
    } catch {}

    if (job.file_path) {
      try {
        const windowsPath = convertToWindowsPath(job.file_path);
        await navigator.clipboard.writeText(windowsPath);
        show('Copied Windows path to clipboard');
      } catch {
        // fallback
      }
    }
  };

  const handleResendEmail = async () => {
    if (!resendStaffName) {
      show('Please select your name');
      return;
    }
    
    try {
      setIsResendingConfirm(true);
      const response = await apiClient.post<any>(`/api/v1/jobs/${job.id}/admin/resend-email`, { 
        staff_name: resendStaffName 
      });
      
      if (response && (response as any).message) {
        show('Confirmation email resent successfully');
      } else {
        show('Email sent but no confirmation received');
      }
      
      setShowResendModal(false);
    } catch (e: any) {
      const errorMessage = e?.message || 'Failed to resend confirmation email';
      show(`Error: ${errorMessage}`);
    } finally {
      setIsResendingConfirm(false);
    }
  };

  return (
    <>
      <div className="flex flex-wrap items-center mt-4 gap-2">
        <div className="flex flex-wrap gap-2">
          {/* UPLOADED status actions */}
          {currentStatus === JobStatus.UPLOADED && (
            <>
              <button
                onClick={onApprove}
                disabled={isApproving || isRejecting}
                className="flex items-center px-3 py-1 bg-green-100 text-green-700 rounded-lg hover:bg-green-200 disabled:opacity-50 focus-ring btn-transition whitespace-nowrap"
              >
                {isApproving ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-2 border-green-600 border-t-transparent mr-1"></div>
                    <span className="hidden sm:inline">Approving...</span>
                  </>
                ) : (
                  <>
                    <CheckCircle className="w-4 h-4 mr-1" />
                    <span className="hidden sm:inline">Approve</span>
                  </>
                )}
              </button>
              <button
                onClick={onReject}
                disabled={isRejecting || isApproving}
                className="flex items-center px-3 py-1 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 disabled:opacity-50 focus-ring btn-transition whitespace-nowrap"
              >
                {isRejecting ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-2 border-red-600 border-t-transparent mr-1"></div>
                    <span className="hidden sm:inline">Rejecting...</span>
                  </>
                ) : (
                  <>
                    <XCircle className="w-4 h-4 mr-1" />
                    <span className="hidden sm:inline">Reject</span>
                  </>
                )}
              </button>
            </>
          )}

          {/* PENDING status actions */}
          {currentStatus === "PENDING" && (
            <button
              onClick={() => {
                setShowResendModal(true);
                setResendStaffName("");
              }}
              className="flex items-center px-3 py-1 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 focus-ring btn-transition whitespace-nowrap"
              title="Resend confirmation email"
              aria-label="Resend confirmation email"
            >
              <Mail className="w-4 h-4 mr-1" />
              <span className="hidden sm:inline">Resend</span>
            </button>
          )}

          {/* READYTOPRINT status actions */}
          {currentStatus === JobStatus.READYTOPRINT && (
            <button
              onClick={() => {
                onStatusChange({
                  action: "mark-printing",
                  title: "Mark as Printing",
                  description: "This will mark the job as currently being printed.",
                  confirmVerb: "Mark Printing"
                });
              }}
              className="flex items-center px-3 py-1 bg-purple-100 text-purple-700 rounded-lg hover:bg-purple-200 focus-ring btn-transition whitespace-nowrap"
            >
              <Printer className="w-4 h-4 mr-1" />
              <span className="hidden sm:inline">Mark Printing</span>
            </button>
          )}

          {/* PRINTING status actions */}
          {currentStatus === JobStatus.PRINTING && (
            <button
              onClick={() => {
                onStatusChange({
                  action: "mark-complete",
                  title: "Mark as Complete",
                  description: "This will mark the job as completed and ready for pickup.",
                  confirmVerb: "Mark Complete"
                });
              }}
              className="flex items-center px-3 py-1 bg-green-100 text-green-700 rounded-lg hover:bg-green-200 focus-ring btn-transition whitespace-nowrap"
            >
              <CheckCircle className="w-4 h-4 mr-1" />
              <span className="hidden sm:inline">Mark Complete</span>
            </button>
          )}

          {/* COMPLETED status actions */}
          {currentStatus === JobStatus.COMPLETED && (
            <button
              onClick={onPayment}
              className="flex items-center px-3 py-1 bg-green-100 text-green-700 rounded-lg hover:bg-green-200 focus-ring btn-transition whitespace-nowrap"
            >
              <CheckCircle className="w-4 h-4 mr-1" />
              <span className="hidden sm:inline">Record Payment</span>
            </button>
          )}

          {/* Open File button (available for all statuses) */}
          <button
            type="button"
            onClick={onOpenFile}
            className="flex items-center px-3 py-1 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 focus-ring btn-transition whitespace-nowrap"
            title="Open File"
          >
            <ExternalLink className="w-4 h-4 mr-1" />
            <span className="hidden sm:inline">Open File</span>
          </button>

          {/* Archive button (available for active statuses) */}
          {([JobStatus.UPLOADED, JobStatus.PENDING, JobStatus.READYTOPRINT, JobStatus.PRINTING, JobStatus.COMPLETED].includes(currentStatus as JobStatus)) && (
            <button
              onClick={onDelete}
              disabled={isDeleting}
              className="flex items-center px-3 py-1 bg-orange-100 text-orange-700 rounded-lg hover:bg-orange-200 disabled:opacity-50 focus-ring btn-transition whitespace-nowrap"
              title="Archive job"
            >
              {isDeleting ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-2 border-orange-600 border-t-transparent mr-1"></div>
                  <span className="hidden sm:inline">Archiving...</span>
                </>
              ) : (
                <>
                  <Archive className="w-4 h-4 mr-1" />
                  <span className="hidden sm:inline">Archive</span>
                </>
              )}
            </button>
          )}
        </div>
      </div>

      {/* Resend Email Modal */}
      {showResendModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="absolute inset-0 bg-black/40" onClick={() => setShowResendModal(false)} />
          <div className="relative bg-white w-full max-w-md rounded-xl shadow-lg border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Resend Confirmation Email</h3>
            <p className="text-sm text-gray-600 mb-4">
              This will send a new confirmation email to the student for job{' '}
              <span className="font-mono">{job.short_id || job.id?.slice(0,8)}</span>.
            </p>
            
            <div className="space-y-4">
              <div>
                <label htmlFor={`resendStaff-${job.id}`} className="block text-sm text-gray-700 mb-1">
                  Performing Action As
                </label>
                <select
                  id={`resendStaff-${job.id}`}
                  className="w-full border rounded-lg px-3 py-2 focus-ring text-sm"
                  value={resendStaffName}
                  onChange={(e) => setResendStaffName(e.target.value)}
                  disabled={loadingStaff}
                >
                  <option value="" disabled>
                    {loadingStaff ? 'Loading staff...' : 'Select your name'}
                  </option>
                  {staff.map(s => (
                    <option key={s.name} value={s.name}>{s.name}</option>
                  ))}
                </select>
              </div>
              
              <div className="flex items-center justify-end space-x-2">
                <button 
                  onClick={() => setShowResendModal(false)}  
                  className="px-3 py-2 rounded-lg border text-gray-700 hover:bg-gray-50 focus-ring btn-transition"
                >
                  Cancel
                </button>
                <button 
                  onClick={handleResendEmail}
                  disabled={isResendingConfirm || !resendStaffName}
                  className="px-3 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 focus-ring btn-transition"
                >
                  {isResendingConfirm ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent mr-2"></div>
                      Resending...
                    </>
                  ) : (
                    'Resend Email'
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
