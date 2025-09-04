"use client";
import React, { useState, useEffect } from 'react';
import { ChevronDown, ChevronUp } from "lucide-react";
import { useToast } from "../ui/toast";
import ReviewModal from './modals/review-modal';
import RejectionModal from './modals/rejection-modal';
import ApprovalModal from './modals/approval-modal';
import StatusChangeModal from './modals/status-change-modal';
import PaymentModal from './modals/payment-modal';
import ConfirmDialog from './modals/confirm-dialog';
import ArchiveJobDialog from './modals/archive-job-dialog';
import { apiClient } from '../../lib/unified-api-client';
import { Job, JobCardProps, JobStatus, JobStatusAction } from '../../types';
import { useModalStore, useJobOperationsStore } from '../../store';
import { JobCardHeader } from './job-card-header';
import { JobCardNotes } from './job-card-notes';
import { JobCardActions } from './job-card-actions';
import { JobCardDetails } from './job-card-details';

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

export default function JobCard({ 
  job, 
  currentStatus = JobStatus.UPLOADED, 
  onApprove, 
  onReject, 
  onMarkReviewed, 
  onStatusAction, 
  onUpdate, 
  onDelete, 
  onModalOpenChange, 
  expandSignal, 
  collapseSignal 
}: JobCardProps) {
  
  const isLocked = typeof job.locked_by === 'string' && job.locked_until !== undefined && new Date(job.locked_until) > new Date();
  
  // Global state stores (leveraging Task 3's completed global state management)
  const modalStore = useModalStore();
  const jobOpsStore = useJobOperationsStore();
  
  // Local component state (focused on coordination)
  const [showMore, setShowMore] = useState(false);
  const [jobNotes, setJobNotes] = useState<string>(job.notes || "");
  const [staff, setStaff] = useState<{ name: string; is_active: boolean }[]>([]);
  const [loadingStaff, setLoadingStaff] = useState(false);
  
  // Job operation states (can be migrated to global state in future)
  const [isApproving, setIsApproving] = useState(false);
  const [isRejecting, setIsRejecting] = useState(false);
  const [isMarkingReviewed, setIsMarkingReviewed] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  
  // Modal states (can be migrated to global modal store)
  const [showReviewModal, setShowReviewModal] = useState<null | { reviewed: boolean }>(null);
  const [showRejectModal, setShowRejectModal] = useState(false);
  const [showApprovalModal, setShowApprovalModal] = useState(false);
  const [showStatusChangeModal, setShowStatusChangeModal] = useState<null | { action: string, title: string, description: string, confirmVerb: string }>(null);
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [openFileModal, setOpenFileModal] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const { show } = useToast();
  const isUnreviewed = currentStatus === JobStatus.UPLOADED && !job.staff_viewed_at;
  const detailsSectionId = `details-section-${job.id}`;
  

  // Respond to global expand/collapse signals
  useEffect(() => {
    if (typeof expandSignal === 'number' && expandSignal > 0) {
      setShowMore(true);
    }
  }, [expandSignal]);

  useEffect(() => {
    if (typeof collapseSignal === 'number' && collapseSignal > 0) {
      setShowMore(false);
    }
  }, [collapseSignal]);

  // Load staff for admin actions and modals
  useEffect(() => {
    const loadStaff = async () => {
      try {
        setLoadingStaff(true);
        const data = await apiClient.get<any>('/api/v1/staff');
        const activeStaff = (data?.staff || []).filter((s: any) => s.is_active);
        setStaff(activeStaff);
      } catch (e) {
        // Fallback handled in individual components
      } finally {
        setLoadingStaff(false);
      }
    };
    loadStaff();
  }, []);

  // Auto-lock and extend lock while any modal is open
  useEffect(() => {
    const isModalOpen = Boolean(
      showReviewModal !== null ||
      showRejectModal ||
      showApprovalModal ||
      showStatusChangeModal !== null ||
      showPaymentModal ||
      showDeleteConfirm ||
      openFileModal
    );

    let intervalId: NodeJS.Timeout;
    const lockJob = async () => {
      try {
        await apiClient.post(`/api/v1/jobs/${job.id}/lock`);
      } catch (err) {
        // Silently handle lock request failures
      }
    };
    const extendLock = async () => {
      try {
        await apiClient.post(`/api/v1/jobs/${job.id}/extend`);
      } catch (err) {
        // Silently handle extend lock failures
      }
    };

    if (isModalOpen) {
      lockJob();
      intervalId = setInterval(extendLock, 4 * 60 * 1000);
    } else {
      apiClient.post(`/api/v1/jobs/${job.id}/unlock`).catch(() => {});
    }

    return () => {
      clearInterval(intervalId);
      apiClient.post(`/api/v1/jobs/${job.id}/unlock`).catch(() => {});
    };
  }, [showReviewModal, showRejectModal, showApprovalModal, showStatusChangeModal, showPaymentModal, showDeleteConfirm, openFileModal, job.id]);

  // Handler functions
  const handleApprove = () => setShowApprovalModal(true);
  const handleReject = () => setShowRejectModal(true);
  const handleMarkReviewed = () => setShowReviewModal({ reviewed: true });
  const handleReapplyNew = () => setShowReviewModal({ reviewed: false });
  const handleExpandAndEditNotes = () => setShowMore(true);
  const handleStatusChange = (config: { action: string; title: string; description: string; confirmVerb: string }) => {
    setShowStatusChangeModal(config);
  };
  const handlePayment = () => setShowPaymentModal(true);
  const handleDelete = () => setShowDeleteConfirm(true);
  const handleOpenFile = () => {
    setOpenFileModal(true);
    // Fix: Remove onModalOpenChange?.(true) call that was causing component remounting
  };

  const copyFilePath = async () => {
    try {
      await apiClient.post(`/api/v1/jobs/${job.id}/log-file-open`, {});
    } catch {}

    if (job.file_path) {
      try {
        const windowsPath = convertToWindowsPath(job.file_path);
        await navigator.clipboard.writeText(windowsPath);
        show('Copied Windows path to clipboard');
      } catch {}
    }
  };

  return (
    <div
      className={`
        bg-white rounded-xl shadow-sm border transition-all card-hover
        ${isUnreviewed ? "border-orange-400 shadow-orange-100 animate-pulse-subtle" : "border-gray-200 hover:border-gray-300"}
        ${isLocked ? "opacity-50 pointer-events-none" : ""}
      `}
    >
      <div className="p-4">
        {/* Job Header Component */}
        <JobCardHeader
          job={job}
          currentStatus={currentStatus}
          isUnreviewed={isUnreviewed}
          isLocked={isLocked}
          jobNotes={jobNotes}
          isMarkingReviewed={isMarkingReviewed}
          onMarkReviewed={handleMarkReviewed}
          onReapplyNew={handleReapplyNew}
          onExpandAndEditNotes={handleExpandAndEditNotes}
        />

        {/* Expandable Details Section */}
        <div
          id={detailsSectionId}
          className={`overflow-hidden transition-all duration-300 ease-in-out ${showMore ? 'max-h-[2000px] opacity-100' : 'max-h-0 opacity-0'}`}
          aria-hidden={!showMore}
        >
          {/* Job Notes Component */}
          <JobCardNotes
            job={job}
            jobNotes={jobNotes}
            onNotesUpdated={setJobNotes}
            staff={staff}
            loadingStaff={loadingStaff}
          />

          {/* Job Details Component */}
          <JobCardDetails
            job={job}
            currentStatus={currentStatus}
          />
        </div>

        {/* Job Actions Component */}
        <JobCardActions
          job={job}
          currentStatus={currentStatus}
          isApproving={isApproving}
          isRejecting={isRejecting}
          isDeleting={isDeleting}
          staff={staff}
          loadingStaff={loadingStaff}
          onApprove={handleApprove}
          onReject={handleReject}
          onStatusChange={handleStatusChange}
          onPayment={handlePayment}
          onDelete={handleDelete}
          onOpenFile={handleOpenFile}
        />

        {/* Collapse/Expand Toggle */}
        <div className="flex justify-center mt-4 pt-2 border-t border-gray-100">
          <button 
            onClick={() => setShowMore(!showMore)} 
            className="flex items-center px-3 py-1 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 focus-ring btn-transition"
            aria-expanded={showMore}
            aria-controls={detailsSectionId}
            aria-label={showMore ? 'Collapse details' : 'Expand details'}
            title={showMore ? 'Collapse' : 'Expand'}
          >
            {showMore ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* Modal Components (unchanged for compatibility) */}
      {showReviewModal && (
        <ReviewModal
          jobId={job.id}
          reviewed={showReviewModal.reviewed}
          onClose={() => setShowReviewModal(null)}
          onUpdated={(updatedJob) => {
            onMarkReviewed?.(job.id, updatedJob);
            setShowReviewModal(null);
          }}
        />
      )}
      
      {showRejectModal && (
        <RejectionModal
          jobId={job.id}
          onClose={() => setShowRejectModal(false)}
          onRejected={() => {
            onReject?.(job.id);
            setShowRejectModal(false);
          }}
        />
      )}
      
      {showApprovalModal && (
        <ApprovalModal
          jobId={job.id}
          material={job.material}
          currentPrinter={job.printer}
          onClose={() => setShowApprovalModal(false)}
          onApproved={() => {
            onApprove?.(job.id);
            setShowApprovalModal(false);
          }}
        />
      )}

      {/* Open File Modal */}
      {openFileModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="absolute inset-0 bg-black/40" onClick={() => {
            setOpenFileModal(false);
            onModalOpenChange?.(false);
          }} />
          <div className="relative bg-white w-full max-w-sm rounded-xl shadow-lg border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Open File</h3>
            <p className="text-sm text-gray-600 mb-3">This logs the action, then opens via the local protocol handler or copies the path.</p>
            <div className="flex flex-col gap-2">
              <a 
                href={`print3d://open/?path=${encodeURIComponent(convertToWindowsPath(job.file_path || ''))}`}
                className="flex items-center justify-center px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 focus-ring btn-transition"
                onClick={async (e) => {
                  try {
                    await apiClient.post(`/api/v1/jobs/${job.id}/log-file-open`, {});
                  } catch {}
                  setTimeout(() => {
                    setOpenFileModal(false);
                    onModalOpenChange?.(false);
                  }, 100);
                }}
              >
                Open in Slicer
              </a>
              <button 
                onClick={copyFilePath} 
                className="flex items-center justify-center px-4 py-2 rounded-lg bg-gray-100 text-gray-800 hover:bg-gray-200 focus-ring btn-transition"
              >
                Copy File Path
              </button>
            </div>
            <div className="mt-3 text-right">
              <button 
                onClick={() => {
                  setOpenFileModal(false);
                  onModalOpenChange?.(false);
                }} 
                className="px-3 py-2 rounded-lg border text-gray-700 hover:bg-gray-50 focus-ring btn-transition"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation */}
      {showDeleteConfirm && (
        <ArchiveJobDialog
          jobShortId={job.short_id || job.id?.slice(0, 6) || ''}
          onCancel={() => setShowDeleteConfirm(false)}
          onConfirm={async (staffName: string) => {
            try {
              setIsDeleting(true);
              await apiClient.delete(`/api/v1/jobs/${job.id}`, {
                staff_name: staffName
              });
              show('Job archived');
              onReject?.(job.id);
            } catch (e) {
              show('Failed to archive job');
            } finally {
              setIsDeleting(false);
              setShowDeleteConfirm(false);
            }
          }}
        />
      )}

      {/* Status Change Modal */}
      {showStatusChangeModal && (
        <StatusChangeModal
          jobId={job.id}
          action={showStatusChangeModal.action as JobStatusAction}
          title={showStatusChangeModal.title}
          description={showStatusChangeModal.description}
          confirmVerb={showStatusChangeModal.confirmVerb}
          onClose={() => setShowStatusChangeModal(null)}
          onSuccess={() => {
            onReject?.(job.id);
            setShowStatusChangeModal(null);
          }}
        />
      )}

      {/* Payment Modal */}
      {showPaymentModal && (
        <PaymentModal
          jobId={job.id}
          onClose={() => setShowPaymentModal(false)}
          onSuccess={() => {
            onReject?.(job.id);
            setShowPaymentModal(false);
          }}
        />
      )}
    </div>
  );
}
