"use client";
import React, { useState, useRef, useEffect } from 'react';
import { User, Mail, Printer, Palette, FileText, CheckCircle, XCircle, Eye, EyeOff, ExternalLink, Copy, Archive, ChevronDown, ChevronUp } from "lucide-react";
import { useToast } from "../ui/toast";
import ReviewModal from './modals/review-modal';
import RejectionModal from './modals/rejection-modal';
import ApprovalModal from './modals/approval-modal';
import StatusChangeModal from './modals/status-change-modal';
import PaymentModal from './modals/payment-modal';
import ConfirmDialog from './modals/confirm-dialog';
import { TooltipProvider, Tooltip, TooltipTrigger, TooltipContent } from "../ui/tooltip";
import { getLegacyToken } from '../../lib/auth';
import { apiClient } from '../../lib/unified-api-client';
import { createErrorState, updateErrorState, clearErrorState } from '../../lib/error-handling';
import { InlineError } from '../ui/error-display';
import { Job, JobCardProps, JobStatus, JobStatusAction, StatusChangeModalConfig, ReviewModalState } from '../../types';

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

export default function JobCard({ job, currentStatus = JobStatus.UPLOADED, onApprove, onReject, onMarkReviewed, onStatusAction, onUpdate, onDelete, onModalOpenChange, expandSignal, collapseSignal }: JobCardProps) {
  const isLocked = typeof job.locked_by === 'string' && job.locked_until !== undefined && new Date(job.locked_until) > new Date();
  
  const [showMore, setShowMore] = useState(false);
  const MAX_NOTES_LEN = 5000;
  const [jobNotes, setJobNotes] = useState<string>(job.notes || "");
  const [isEditingNotes, setIsEditingNotes] = useState(false);
  const [notesDraft, setNotesDraft] = useState<string>("");
  const [staff, setStaff] = useState<{ name: string; is_active: boolean }[]>([]);
  const [loadingStaff, setLoadingStaff] = useState(false);
  const [notesStaffName, setNotesStaffName] = useState<string>("");
  const [savingNotes, setSavingNotes] = useState(false);
  const [saveMessage, setSaveMessage] = useState<string>("");
  const [saveError, setSaveError] = useState(createErrorState());
  const [isApproving, setIsApproving] = useState(false);
  const [isRejecting, setIsRejecting] = useState(false);
  const [isMarkingReviewed, setIsMarkingReviewed] = useState(false);
  const [isResendingConfirm, setIsResendingConfirm] = useState(false);
  const [showReviewModal, setShowReviewModal] = useState<null | { reviewed: boolean }>(null);
  const [showRejectModal, setShowRejectModal] = useState(false);
  const [showApprovalModal, setShowApprovalModal] = useState(false);
  const [showStatusChangeModal, setShowStatusChangeModal] = useState<null | { action: string, title: string, description: string, confirmVerb: string }>(null);
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [openFileModal, setOpenFileModal] = useState(false);
  const { show } = useToast();
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [adminStaffName, setAdminStaffName] = useState<string>("");
  const [showResendModal, setShowResendModal] = useState(false);
  const [resendStaffName, setResendStaffName] = useState<string>("");
  const notesHeaderRef = useRef<HTMLHeadingElement | null>(null);
  const notesSectionId = `notes-section-${job.id}`;
  const notesTextareaRef = useRef<HTMLTextAreaElement | null>(null);
  const detailsSectionId = `details-section-${job.id}`;

  // Focus the textarea when entering edit mode for quick typing
  useEffect(() => {
    if (isEditingNotes) {
      setTimeout(() => notesTextareaRef.current?.focus(), 0);
    }
  }, [isEditingNotes]);

  // Respond to global expand/collapse signals
  useEffect(() => {
    if (typeof expandSignal === 'number' && expandSignal > 0) {
      // Open details
      setShowMore(true);
    }
  }, [expandSignal]);

  useEffect(() => {
    if (typeof collapseSignal === 'number' && collapseSignal > 0) {
      // Close details
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
        setStaff(activeStaff); // Set staff state for all modals
        if (activeStaff.length > 0) {
          setAdminStaffName(activeStaff[0].name);
        }
      } catch (e) {
        // Fallback to 'Admin User' if staff loading fails
        setAdminStaffName('Admin User');
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
      showResendModal
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
      apiClient.post(`/api/v1/jobs/${job.id}/unlock`).catch(() => {
        // Silently handle unlock failures
      });
    }

    return () => {
      clearInterval(intervalId);
      apiClient.post(`/api/v1/jobs/${job.id}/unlock`).catch(() => {
        // Silently handle unlock failures
      });
    };
  }, [showReviewModal, showRejectModal, showApprovalModal, showStatusChangeModal, showPaymentModal, showDeleteConfirm, showResendModal, job.id]);

  // Staff data is already loaded on component mount, no need for separate resend modal loading
  
  const isUnreviewed = currentStatus === JobStatus.UPLOADED && !job.staff_viewed_at;

  // Calculate job age and determine color
  const getAgeColor = (createdAt: string) => {
    const ageInHours = (Date.now() - new Date(createdAt).getTime()) / (1000 * 60 * 60);

    if (ageInHours < 24) return "text-green-600";
    if (ageInHours < 48) return "text-yellow-600";
    if (ageInHours < 72) return "text-orange-600";
    return "text-red-600";
  };

  const ageColor = job.created_at ? getAgeColor(job.created_at) : "text-gray-500";

  // Exact elapsed formatter: days, hours, minutes (no rounding)
  const formatElapsed = (createdAt: string) => {
    const created = new Date(createdAt);
    const now = new Date();
    const diffMs = Math.max(0, now.getTime() - created.getTime());
    const totalMinutes = Math.floor(diffMs / 60000);
    if (totalMinutes < 1) return 'Submitted just now';

    const minutesPerDay = 60 * 24;
    const days = Math.floor(totalMinutes / minutesPerDay);
    const hours = Math.floor((totalMinutes % minutesPerDay) / 60);
    const minutes = totalMinutes % 60;

    const parts: string[] = [];
    if (days > 0) parts.push(`${days}d`);
    if (hours > 0) parts.push(`${hours}h`);
    if (minutes > 0) parts.push(`${minutes}m`);

    if (parts.length === 0) return 'Submitted just now';
    return `Submitted ${parts.join(' ')} ago`;
  };
  const timeElapsed = job.created_at ? formatElapsed(job.created_at) : 'Submitted recently';

  // Format created timestamp explicitly in Baton Rouge, Louisiana timezone (America/Chicago)
  const formatCreatedAtCentral = (createdAt?: string) => {
    if (!createdAt) return 'Unknown';
    try {
      const dt = new Date(createdAt);
      return new Intl.DateTimeFormat('en-US', {
        timeZone: 'America/Chicago',
        year: 'numeric',
        month: 'short',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        hour12: true,
      }).format(dt);
    } catch {
      return 'Unknown';
    }
  };

  const handleApprove = async () => {
    setShowApprovalModal(true);
  };

  const handleReject = async () => {
    setShowRejectModal(true);
  };

  const handleMarkReviewed = () => {
    setShowReviewModal({ reviewed: true });
  };

  const handleReapplyNew = () => {
    setShowReviewModal({ reviewed: false });
  };

  const beginEditNotes = async () => {
    setIsEditingNotes(true);
    setNotesDraft("");
    setSaveMessage("");
    setSaveError(clearErrorState());
    // REMOVED: onModalOpenChange?.(true); - Notes editing doesn't need auto-refresh pause like real modals
    // Staff is already loaded on component mount
  };

  const cancelEditNotes = () => {
    setIsEditingNotes(false);
    setNotesDraft(jobNotes || "");
    setNotesStaffName("");
    setSaveMessage("");
    setSaveError(clearErrorState());
    // REMOVED: onModalOpenChange?.(false); - Notes editing doesn't need auto-refresh pause like real modals
  };

  const openOpenFileModal = async () => {
    setOpenFileModal(true);
    onModalOpenChange?.(true);
  };

  const closeOpenFileModal = () => {
    setOpenFileModal(false);
    onModalOpenChange?.(false);
  };

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
    // Keep modal open for test visibility; user can close manually.
  };

  const saveNotes = async () => {
    if (!notesStaffName) {
      setSaveError(updateErrorState(saveError, new Error('Please select your name before saving.')));
      return;
    }
    const MAX_ENTRY_LEN = 1000;
    if (notesDraft.length === 0) {
      setSaveError(updateErrorState(saveError, new Error('Please enter a note.')));
      return;
    }
    if (notesDraft.length > MAX_ENTRY_LEN) {
      setSaveError(updateErrorState(saveError, new Error(`Note must be at most ${MAX_ENTRY_LEN} characters.`)));
      return;
    }
    try {
      setSavingNotes(true);
      setSaveError(clearErrorState());
      setSaveMessage("Saving...");
      const data = await apiClient.post<{ notes?: string }>(`/api/v1/jobs/${job.id}/notes`, { text: notesDraft, staff_name: notesStaffName });
      setJobNotes(data?.notes || (jobNotes ? `${jobNotes}\n${notesDraft}` : notesDraft));
      setSaveMessage('Saved');
      setIsEditingNotes(false);
      setNotesDraft("");
      // REMOVED: onModalOpenChange?.(false); - Notes saving doesn't need auto-refresh pause like real modals
    } catch (e) {
      setSaveError(updateErrorState(saveError, e));
    } finally {
      setSavingNotes(false);
      setTimeout(() => setSaveMessage(""), 1500);
    }
  };
  // Removed autosave; composer uses explicit submit to POST append

  return (
    <TooltipProvider>
         <div
       className={`
       bg-white rounded-xl shadow-sm border transition-all card-hover
       ${isUnreviewed ? "border-orange-400 shadow-orange-100 animate-pulse-subtle" : "border-gray-200 hover:border-gray-300"}
       ${isLocked ? "opacity-50 pointer-events-none" : ""}
     `}
     >
       <div className="p-4">
    {isLocked && (
      <div className="mb-2 text-sm text-red-600 font-medium">
        🔒 Locked by {job.locked_by}
      </div>
    )}
		        {currentStatus === JobStatus.UPLOADED && isUnreviewed && (
          <div className="flex items-center justify-between mb-3">
				<span className="bg-orange-200 text-orange-900 text-xs font-semibold px-2 py-1 rounded-full">NEW</span>
            <Tooltip>
              <TooltipTrigger asChild>
                <button
                  onClick={handleMarkReviewed}
                  disabled={isMarkingReviewed}
                  className="text-xs text-gray-500 hover:text-gray-700 flex items-center disabled:opacity-50 focus-ring btn-transition"
                  title="Mark as reviewed (hides NEW badge)"
                  aria-label="Mark as reviewed (hides NEW badge)"
                >
                  {isMarkingReviewed ? (
                    <>
                      <div className="animate-spin rounded-full h-3 w-3 border border-gray-400 border-t-transparent mr-1"></div>
                      Marking...
                    </>
                  ) : (
                    <>
                      <Eye className="w-3 h-3 mr-1" />
                      Reviewed
                    </>
                  )}
                </button>
              </TooltipTrigger>
              <TooltipContent side="left">Marks this job as reviewed (hides NEW badge)</TooltipContent>
            </Tooltip>
          </div>
        )}

        <div className="flex justify-between items-start mb-3">
          <h3 className="text-lg font-semibold text-gray-900 truncate">{job.student_name || job.display_name || (job.short_id || job.id?.slice(0,8) + '…')}</h3>
          <span className={`text-sm ${ageColor} font-medium`}>{timeElapsed}</span>
        </div>

        <p className="text-gray-600 text-sm mb-3 truncate">{job.display_name || job.original_filename || 'Unknown file'}</p>

        <div className="grid grid-cols-2 gap-2 mb-3 items-start">
          {/* Email */}
          <div className="flex items-center text-sm text-gray-500">
            <Mail className="w-4 h-4 mr-1" />
            <span className="truncate">{job.student_email || 'No email'}</span>
          </div>
          {/* Printer */}
          <div className="flex items-center text-sm text-gray-500">
            <Printer className="w-4 h-4 mr-1" />
            <span className="truncate">{job.printer || 'Not set'}</span>
          </div>
          {/* Color */}
          <div className="flex items-center text-sm text-gray-500">
            <Palette className="w-4 h-4 mr-1" />
            <span className="truncate">{job.color || 'Not set'}</span>
          </div>
          {/* Notes indicator (fixed cell for grid consistency) */}
          <div className="text-sm text-gray-500">
            {jobNotes ? (
              <button
                type="button"
                onClick={() => {
                                  setShowMore(true);
                  beginEditNotes();
                  // Focus will move to textarea via effect
                }}
                className="flex items-center text-sm text-gray-500 hover:text-gray-700 focus-ring btn-transition"
                title="Has notes — click to add or edit"
                aria-label="Has notes — click to add or edit"
                aria-expanded={showMore}
                aria-controls={notesSectionId}
              >
                <FileText className="w-4 h-4 mr-1" />
                <span className="hidden md:inline font-medium">Has notes</span>
              </button>
            ) : (
              <div
                className="flex items-center text-sm text-gray-500 invisible select-none"
                aria-hidden="true"
              >
                <FileText className="w-4 h-4 mr-1" />
                <span className="hidden md:inline font-medium">Has notes</span>
              </div>
            )}
          </div>
        </div>


        <div
          id={detailsSectionId}
          className={`overflow-hidden transition-all duration-300 ease-in-out ${showMore ? 'max-h-[2000px] opacity-100' : 'max-h-0 opacity-0'}`}
          aria-hidden={!showMore}
          aria-labelledby={notesSectionId}
        >
          <div className="mt-3 pt-3 border-t border-gray-100">
            {/* Staff Notes section */}
            <div id={notesSectionId}>
              <div className="flex items-center justify-between mb-2">
                <h4
                  ref={notesHeaderRef}
                  tabIndex={-1}
                  className="text-sm font-medium text-gray-900 focus:outline-none"
                >
                  Staff Notes
                </h4>
              </div>
              {!isEditingNotes && !jobNotes && (
                <div
                  className="text-sm text-gray-500 italic mb-3 cursor-pointer focus-ring"
                  role="button"
                  tabIndex={0}
                  onClick={() => {
    
                    beginEditNotes();
                  }}
                  onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); beginEditNotes(); } }}
                  aria-label="Click to add a note"
                >
                  No notes added yet — click to add
                </div>
              )}
              {jobNotes && !isEditingNotes && (
                <div className="mb-4">
                  <div
                    className="bg-gray-50 p-2 rounded border cursor-pointer focus-ring"
                    role="button"
                    tabIndex={0}
                    onClick={() => {
      
                      beginEditNotes();
                    }}
                    onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); beginEditNotes(); } }}
                    aria-label="Click to add or edit note"
                  >
                    <ul className="list-disc ml-5 space-y-1 text-sm text-gray-900">
                      {(jobNotes.split('\n').filter(Boolean).reverse()).map((line, idx) => (
                        <li key={idx}>{line}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}
              {isEditingNotes && (
                <div className="mt-1 space-y-3">
                  {jobNotes && (
                    <div>
                      <span className="text-gray-500 text-sm">Existing notes:</span>
                      <div className="bg-gray-50 p-2 rounded border mt-1">
                        <ul className="list-disc ml-5 space-y-1 text-sm text-gray-900">
                          {(jobNotes.split('\n').filter(Boolean).reverse()).map((line, idx) => (
                            <li key={idx}>{line}</li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  )}
                                     <div className="px-1">
                     <label htmlFor={`notes-${job.id}`} className="text-gray-500 text-sm block mb-1">Add a new note</label>
                     <textarea
                       id={`notes-${job.id}`}
                       className="w-full min-h-[100px] border rounded-lg px-3 py-2 focus-ring text-sm"
                       value={notesDraft}
                       onChange={(e) => setNotesDraft(e.target.value)}
                       aria-describedby={`notes-status-${job.id}`}
                       placeholder="Type your note to append…"
                       ref={notesTextareaRef}
                     />
                     <div className="mt-1 text-xs text-gray-500">{notesDraft.length}/{MAX_NOTES_LEN}</div>
                   </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                    <div>
                      <label htmlFor={`notesStaff-${job.id}`} className="block text-sm text-gray-700 mb-1">Performing Action As</label>
                      <select
                        id={`notesStaff-${job.id}`}
                        className="w-full border rounded-lg px-3 py-2 focus-ring text-sm"
                        value={notesStaffName}
                        onChange={(e) => setNotesStaffName(e.target.value)}
                        disabled={loadingStaff}
                      >
                        <option value="" disabled>{loadingStaff ? 'Loading staff...' : 'Select your name'}</option>
                        {staff.map(s => (
                          <option key={s.name} value={s.name}>{s.name}</option>
                        ))}
                      </select>
                    </div>
                    <div className="flex items-end justify-end space-x-2">
                      <button onClick={cancelEditNotes} type="button" className="px-3 py-2 rounded-lg border text-gray-700 hover:bg-gray-50 focus-ring btn-transition">Cancel</button>
                      <button onClick={saveNotes} type="button" disabled={savingNotes || !notesStaffName || notesDraft.length > MAX_NOTES_LEN} className="px-3 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 focus-ring btn-transition">{savingNotes ? 'Saving...' : 'Save Notes'}</button>
                    </div>
                  </div>
                  <div id={`notes-status-${job.id}`} className="mt-1 text-sm" aria-live="polite">
                    {saveMessage && <span className="text-green-600">{saveMessage}</span>}
                    {saveError.hasError && (
                      <InlineError
                        error={saveError}
                        className="mt-1"
                      />
                    )}
                    {notesDraft.length > MAX_NOTES_LEN && (
                      <div className="text-red-600" role="alert">Notes must be at most {MAX_NOTES_LEN} characters.</div>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Additional Details */}
            <h4 className="text-sm font-medium text-gray-900 mt-4 mb-2">Additional Details</h4>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div>
                <span className="text-gray-500">Job ID:</span>
                <div className="flex items-center gap-2">
                  <p className="text-gray-900 font-mono" title={job.id}>
                    {job.short_id || (job.id?.slice(0,8) + '…')}
                  </p>
                  <button
                    type="button"
                    className="p-1 rounded bg-gray-100 text-gray-700 hover:bg-gray-200 focus-ring"
                    title="Copy full Job ID"
                    aria-label="Copy Job ID"
                    onClick={async () => {
                      try {
                        await navigator.clipboard.writeText(job.id || '');
                        show('Job ID copied');
                      } catch {}
                    }}
                  >
                    <Copy className="w-3 h-3" />
                  </button>
                </div>
              </div>
              <div>
                <span className="text-gray-500">Created:</span>
                <p className="text-gray-900">{formatCreatedAtCentral(job.created_at)}</p>
              </div>
              <div>
                <span className="text-gray-500">Discipline:</span>
                <p className="text-gray-900">{job.discipline || 'Not set'}</p>
              </div>
              <div>
                <span className="text-gray-500">Class:</span>
                <p className="text-gray-900">{job.class_number || 'Not set'}</p>
              </div>
            </div>
            {(job.weight_g || job.time_hours || job.cost_usd) && (
              <div className="mt-3">
                <h5 className="text-sm font-medium text-gray-900 mb-1">Print Details</h5>
                <div className="grid grid-cols-3 gap-2 text-sm">
                  {typeof job.weight_g === 'number' && (
                    <div className="text-gray-700">
                      <span className="text-gray-500">
                        {currentStatus === JobStatus.PAIDPICKEDUP && job.payment ? 'Final Weight:' : 'Weight:'}
                      </span> 
                      {currentStatus === JobStatus.PAIDPICKEDUP && job.payment ? job.payment.grams : job.weight_g} g
                    </div>
                  )}
                  {typeof job.time_hours === 'number' && (
                    <div className="text-gray-700"><span className="text-gray-500">Time:</span> {job.time_hours} h</div>
                  )}
                  {typeof job.cost_usd === 'number' && (
                    <div className="text-gray-700">
                      <span className="text-gray-500">
                        {currentStatus === JobStatus.PAIDPICKEDUP && job.payment ? 'Final Cost:' : 'Estimated Cost:'}
                      </span> 
                      ${currentStatus === JobStatus.PAIDPICKEDUP && job.payment ? job.payment.price_usd.toFixed(2) : job.cost_usd.toFixed(2)}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>

                 <div className="flex flex-wrap items-center mt-4 gap-2">
           <div className="flex flex-wrap gap-2">
             {currentStatus === JobStatus.UPLOADED && (
               <>
 				{!!job.staff_viewed_at && (
                 <Tooltip>
                   <TooltipTrigger asChild>
                     <button
                       onClick={handleReapplyNew}
                       title="Mark as unreviewed (shows NEW badge again)"
                       aria-label="Mark as unreviewed (shows NEW badge again)"
                       className="flex items-center px-3 py-1 bg-orange-100 text-orange-900 rounded-lg hover:bg-orange-200 hover:text-orange-950 focus-ring btn-transition whitespace-nowrap"
                     >
                                               <EyeOff className="w-4 h-4 mr-1" />
                        <span className="hidden sm:inline">Unreviewed</span>
                     </button>
                   </TooltipTrigger>
                   <TooltipContent side="top">Marks this job as unreviewed (shows NEW badge again)</TooltipContent>
                 </Tooltip>
                 )}
                 <button
                   onClick={handleApprove}
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
                   onClick={handleReject}
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
              {currentStatus === JobStatus.READYTOPRINT && (
                                <button
                   onClick={() => {
                     setShowStatusChangeModal({
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
             <button
               type="button"
               onClick={openOpenFileModal}
               className="flex items-center px-3 py-1 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 focus-ring btn-transition whitespace-nowrap"
               title="Open File"
             >
               <ExternalLink className="w-4 h-4 mr-1" />
               <span className="hidden sm:inline">Open File</span>
             </button>

             {currentStatus === JobStatus.PRINTING && (
                                <button
                   onClick={() => {
                     setShowStatusChangeModal({
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
             {currentStatus === JobStatus.COMPLETED && (
                                           <button
                 onClick={() => {
                   setShowPaymentModal(true);
                 }}
                 className="flex items-center px-3 py-1 bg-green-100 text-green-700 rounded-lg hover:bg-green-200 focus-ring btn-transition whitespace-nowrap"
               >
                 <CheckCircle className="w-4 h-4 mr-1" />
                 <span className="hidden sm:inline">Record Payment</span>
               </button>
             )}
              {([JobStatus.UPLOADED, JobStatus.PENDING, JobStatus.READYTOPRINT, JobStatus.PRINTING, JobStatus.COMPLETED].includes(currentStatus as JobStatus)) && (
                <button
                  onClick={() => setShowDeleteConfirm(true)}
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

         {/* Collapse arrow at bottom center */}
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
      {showReviewModal && (
        <ReviewModal
          jobId={job.id}
          reviewed={showReviewModal.reviewed}
          onClose={() => setShowReviewModal(null)}
          onUpdated={(updatedJob) => {
            // Optimistically reflect returned state in the card via callback to parent when available
            // Fallback: reload page section can be triggered by parent on next refetch
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
            // Delegate to parent to remove from list
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
            // Delegate to parent to remove from list
            onApprove?.(job.id);
            setShowApprovalModal(false);
          }}
        />
      )}
      {openFileModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="absolute inset-0 bg-black/40" onClick={closeOpenFileModal} />
          <div className="relative bg-white w-full max-w-sm rounded-xl shadow-lg border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Open File</h3>
            <p className="text-sm text-gray-600 mb-3">This logs the action, then opens via the local protocol handler or copies the path.</p>
            <div className="flex flex-col gap-2">
              {/* FIXED: Real anchor preserves user gesture for protocol launching */}
              <a 
                href={`print3d://open/?path=${encodeURIComponent(convertToWindowsPath(job.file_path || ''))}`}
                className="flex items-center justify-center px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 focus-ring btn-transition"
                onClick={async (e) => {
                  const windowsPath = convertToWindowsPath(job.file_path || '');
                  
                  // Log the action regardless
                  try {
                    await apiClient.post(`/api/v1/jobs/${job.id}/log-file-open`, {});
                  } catch {}
                  
                  // Fire-and-forget logging (don't block the protocol launch)
                  try {
                    apiClient.post(`/api/v1/jobs/${job.id}/log-file-open`, {}).catch(() => {});
                  } catch {
                    // ignore
                  }
                  
                  // Close modal after click
                  setTimeout(() => closeOpenFileModal(), 100);
                }}
              >
                <ExternalLink className="w-4 h-4 mr-2" /> Open in Slicer
              </a>
              <button onClick={copyFilePath} className="flex items-center justify-center px-4 py-2 rounded-lg bg-gray-100 text-gray-800 hover:bg-gray-200 focus-ring btn-transition">
                <Copy className="w-4 h-4 mr-2" /> Copy File Path
              </button>
            </div>
            <p className="text-xs text-gray-500 mt-3">If nothing happens, install the protocol handler on this machine.</p>
            <div className="mt-3 text-right">
              <button onClick={closeOpenFileModal} className="px-3 py-2 rounded-lg border text-gray-700 hover:bg-gray-50 focus-ring btn-transition">Close</button>
            </div>
          </div>
        </div>
      )}
      {showDeleteConfirm && (
        <ConfirmDialog
          title="Confirm Archive"
          description="This will archive the job. You can later permanently delete it from the Admin area."
          confirmLabel="Archive Job"
          onCancel={() => setShowDeleteConfirm(false)}
          onConfirm={async () => {
            try {
              setIsDeleting(true);
              await apiClient.delete(`/api/v1/jobs/${job.id}`);
              show('Job archived');
              onReject?.(job.id);
            } catch (e) {
              show('Failed to archive job');
            } finally {
              setIsDeleting(false);
              setShowDeleteConfirm(false);
            }
          }}
          requireTextMatch={{
            label: 'Type the Job short ID to confirm',
            expected: job.short_id || (job.id?.slice(0, 6) || ''),
            placeholder: job.short_id || job.id?.slice(0, 6)
                     }}
         />
       )}
       {showResendModal && (
         <div className="fixed inset-0 z-50 flex items-center justify-center">
                       <div className="absolute inset-0 bg-black/40" onClick={() => {
              setShowResendModal(false);
            }} />
           <div className="relative bg-white w-full max-w-md rounded-xl shadow-lg border border-gray-200 p-6">
             <h3 className="text-lg font-semibold text-gray-900 mb-2">Resend Confirmation Email</h3>
             <p className="text-sm text-gray-600 mb-4">This will send a new confirmation email to the student for job <span className="font-mono">{job.short_id || job.id?.slice(0,8)}</span>.</p>
             
             <div className="space-y-4">
               <div>
                 <label htmlFor={`resendStaff-${job.id}`} className="block text-sm text-gray-700 mb-1">Performing Action As</label>
                 <select
                   id={`resendStaff-${job.id}`}
                   className="w-full border rounded-lg px-3 py-2 focus-ring text-sm"
                   value={resendStaffName}
                   onChange={(e) => setResendStaffName(e.target.value)}
                   disabled={loadingStaff}
                 >
                   <option value="" disabled>{loadingStaff ? 'Loading staff...' : 'Select your name'}</option>
                   {staff.map(s => (
                     <option key={s.name} value={s.name}>{s.name}</option>
                   ))}
                 </select>
               </div>
               
               <div className="flex items-center justify-end space-x-2">
                                   <button 
                    onClick={() => {
                      setShowResendModal(false);
                    }}  
                   className="px-3 py-2 rounded-lg border text-gray-700 hover:bg-gray-50 focus-ring btn-transition"
                 >
                   Cancel
                 </button>
                 <button 
                   onClick={async () => {
                     if (!resendStaffName) {
                       show('Please select your name');
                       return;
                     }
                     
                     try {
                       setIsResendingConfirm(true);
                       const response = await apiClient.post<any>(`/api/v1/jobs/${job.id}/admin/resend-email`, { staff_name: resendStaffName });
                       
                       // Check if email was actually sent
                       if (response && (response as any).message) {
                         show('Confirmation email resent successfully');
                       } else {
                         show('Email sent but no confirmation received');
                       }
                       
                                               setShowResendModal(false);
                     } catch (e: any) {
                       // Provide more specific error messages
                       const errorMessage = e?.message || 'Failed to resend confirmation email';
                       show(`Error: ${errorMessage}`);
                       // Silently handle resend email errors
                     } finally {
                       setIsResendingConfirm(false);
                     }
                   }}
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
       {showStatusChangeModal && (
         <StatusChangeModal
           jobId={job.id}
           action={showStatusChangeModal.action as JobStatusAction}
           title={showStatusChangeModal.title}
           description={showStatusChangeModal.description}
           confirmVerb={showStatusChangeModal.confirmVerb}
           onClose={() => {
             setShowStatusChangeModal(null);
           }}
           onSuccess={() => {
             // Remove job from current list since it will move to a different status
             onReject?.(job.id);
             setShowStatusChangeModal(null);
           }}
         />
       )}
       {showPaymentModal && (
         <PaymentModal
           jobId={job.id}
           onClose={() => {
             setShowPaymentModal(false);
           }}
           onSuccess={() => {
             // Remove job from current list since it will move to PAIDPICKEDUP status
             onReject?.(job.id);
             setShowPaymentModal(false);
           }}
         />
       )}
     </div>
     </TooltipProvider>
   );
}