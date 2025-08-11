"use client";
import React, { useState } from 'react';
import { User, Mail, Printer, Palette, FileText, CheckCircle, XCircle, Eye } from "lucide-react";
import ReviewModal from './modals/review-modal';
import RejectionModal from './modals/rejection-modal';

interface Job {
  id: string;
  short_id?: string;
  display_name?: string;
  student_name?: string;
  student_email?: string;
  original_filename?: string;
  printer?: string;
  color?: string;
  material?: string;
  weight_g?: number;
  time_hours?: number;
  cost_usd?: number;
  created_at?: string;
  notes?: string;
  staff_viewed_at?: string;
}

interface JobCardProps {
  job: Job;
  currentStatus?: string;
  onApprove?: (jobId: string) => void;
  onReject?: (jobId: string) => void;
  onMarkReviewed?: (jobId: string) => void;
  onStatusAction?: (jobId: string, action: "mark-printing" | "mark-complete" | "mark-picked-up") => void;
}

export default function JobCard({ job, currentStatus = "UPLOADED", onApprove, onReject, onMarkReviewed, onStatusAction }: JobCardProps) {
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
  const [saveError, setSaveError] = useState<string>("");
  const [isApproving, setIsApproving] = useState(false);
  const [isRejecting, setIsRejecting] = useState(false);
  const [isMarkingReviewed, setIsMarkingReviewed] = useState(false);
  const [showReviewModal, setShowReviewModal] = useState<null | { reviewed: boolean }>(null);
  const [showRejectModal, setShowRejectModal] = useState(false);
  
  const isUnreviewed = currentStatus === 'UPLOADED' && !job.staff_viewed_at;

  // Calculate job age and determine color
  const getAgeColor = (createdAt: string) => {
    const ageInHours = (Date.now() - new Date(createdAt).getTime()) / (1000 * 60 * 60);

    if (ageInHours < 24) return "text-green-600";
    if (ageInHours < 48) return "text-yellow-600";
    if (ageInHours < 72) return "text-orange-600";
    return "text-red-600";
  };

  const ageColor = job.created_at ? getAgeColor(job.created_at) : "text-gray-500";

  // Custom elapsed formatter: 10-min increments up to 2h, then round up to 30-min increments
  const formatElapsed = (createdAt: string) => {
    const created = new Date(createdAt);
    const now = new Date();
    const diffMinutes = Math.max(0, Math.floor((now.getTime() - created.getTime()) / 60000));
    if (diffMinutes < 1) return 'just now';
    const roundUp = (value: number, increment: number) => Math.ceil(value / increment) * increment;
    let roundedMins: number;
    if (diffMinutes < 120) {
      roundedMins = roundUp(diffMinutes, 10);
    } else {
      roundedMins = roundUp(diffMinutes, 30);
    }
    const hours = Math.floor(roundedMins / 60);
    const mins = roundedMins % 60;
    if (hours === 0) return `About ${mins} min ago`;
    if (mins === 0) return `About ${hours} hr ago`;
    return `About ${hours} hr ${mins} min ago`;
  };
  const timeElapsed = job.created_at ? formatElapsed(job.created_at) : 'recently';

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
    setIsApproving(true);
    await new Promise(resolve => setTimeout(resolve, 1000)); // Simulate API call
    onApprove?.(job.id);
    setIsApproving(false);
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
    setSaveError("");
    // lazy-load staff
    try {
      setLoadingStaff(true);
      const token = localStorage.getItem('token');
      const res = await fetch('/api/v1/staff', { headers: { Authorization: `Bearer ${token}` } });
      if (!res.ok) throw new Error('Failed to load staff');
      const data = await res.json();
      setStaff((data?.staff || []).filter((s: any) => s.is_active));
    } catch (e) {
      setSaveError('Failed to load staff list');
    } finally {
      setLoadingStaff(false);
    }
  };

  const cancelEditNotes = () => {
    setIsEditingNotes(false);
    setNotesDraft(jobNotes || "");
    setNotesStaffName("");
    setSaveMessage("");
    setSaveError("");
  };

  const saveNotes = async () => {
    if (!notesStaffName) {
      setSaveError('Please select your name before saving.');
      return;
    }
    const MAX_ENTRY_LEN = 1000;
    if (notesDraft.length === 0) {
      setSaveError('Please enter a note.');
      return;
    }
    if (notesDraft.length > MAX_ENTRY_LEN) {
      setSaveError(`Note must be at most ${MAX_ENTRY_LEN} characters.`);
      return;
    }
    try {
      setSavingNotes(true);
      setSaveError("");
      setSaveMessage("Saving...");
      const token = localStorage.getItem('token');
      const res = await fetch(`/api/v1/jobs/${job.id}/notes`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ text: notesDraft, staff_name: notesStaffName })
      });
      if (!res.ok) {
        const txt = await res.text();
        throw new Error(txt || 'Failed to add note');
      }
      const data = await res.json();
      setJobNotes(data?.notes || (jobNotes ? `${jobNotes}\n${notesDraft}` : notesDraft));
      setSaveMessage('Saved');
      setIsEditingNotes(false);
      setNotesDraft("");
    } catch (e) {
      setSaveError('Failed to add note. Please try again.');
    } finally {
      setSavingNotes(false);
      setTimeout(() => setSaveMessage(""), 1500);
    }
  };
  // Removed autosave; composer uses explicit submit to POST append

  return (
    <div
      className={`
      bg-white rounded-xl shadow-sm border transition-all card-hover
      ${isUnreviewed ? "border-orange-400 shadow-orange-100 animate-pulse-subtle" : "border-gray-200 hover:border-gray-300"}
    `}
    >
      <div className="p-4">
        {currentStatus === 'UPLOADED' && isUnreviewed && (
          <div className="flex items-center justify-between mb-3">
            <span className="bg-orange-100 text-orange-800 text-xs font-semibold px-2 py-1 rounded-full">NEW</span>
            <button
              onClick={handleMarkReviewed}
              disabled={isMarkingReviewed}
              className="text-xs text-gray-500 hover:text-gray-700 flex items-center disabled:opacity-50 focus-ring btn-transition"
            >
              {isMarkingReviewed ? (
                <>
                  <div className="animate-spin rounded-full h-3 w-3 border border-gray-400 border-t-transparent mr-1"></div>
                  Marking...
                </>
              ) : (
                <>
                  <Eye className="w-3 h-3 mr-1" />
                  Mark as Reviewed
                </>
              )}
            </button>
          </div>
        )}

        <div className="flex justify-between items-start mb-3">
          <h3 className="text-lg font-semibold text-gray-900 truncate">{job.student_name || job.display_name || (job.short_id || job.id?.slice(0,8) + '…')}</h3>
          <span className={`text-sm ${ageColor} font-medium`}>{timeElapsed}</span>
        </div>

        <p className="text-gray-600 text-sm mb-3 truncate">{job.display_name || job.original_filename || 'Unknown file'}</p>

        <div className="grid grid-cols-2 gap-2 mb-3">
          <div className="flex items-center text-sm text-gray-500">
            <Mail className="w-4 h-4 mr-1" />
            <span className="truncate">{job.student_email || 'No email'}</span>
          </div>
          <div className="text-sm text-gray-500">
            <div className="flex items-center">
              <Printer className="w-4 h-4 mr-1" />
              <span className="truncate">{job.printer || 'Not set'}</span>
            </div>
            {jobNotes && (
              <button
                type="button"
                onClick={() => { setShowMore(true); beginEditNotes(); }}
                className="flex items-center text-sm text-gray-500 hover:text-gray-700 mt-1 focus-ring btn-transition"
                title="Has notes — click to add or edit"
                aria-label="Has notes — click to add or edit"
              >
                <FileText className="w-4 h-4 mr-1" />
                <span className="hidden md:inline font-medium">Has notes</span>
              </button>
            )}
          </div>
          <div className="flex items-center text-sm text-gray-500">
            <Palette className="w-4 h-4 mr-1" />
            <span className="truncate">{job.color || 'Not set'}</span>
          </div>
        </div>

        

        {showMore && (
          <div className="mt-3 pt-3 border-t border-gray-100">
            <h4 className="text-sm font-medium text-gray-900 mb-2">Additional Details</h4>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div>
                <span className="text-gray-500">Job ID:</span>
                <p className="text-gray-900">{job.short_id || (job.id?.slice(0,8) + '…')}</p>
              </div>
              <div>
                <span className="text-gray-500">Created:</span>
                <p className="text-gray-900">{formatCreatedAtCentral(job.created_at)}</p>
              </div>
            </div>
            {(job.weight_g || job.time_hours || job.cost_usd) && (
              <div className="mt-3">
                <h5 className="text-sm font-medium text-gray-900 mb-1">Print Details</h5>
                <div className="grid grid-cols-3 gap-2 text-sm">
                  {typeof job.weight_g === 'number' && (
                    <div className="text-gray-700"><span className="text-gray-500">Weight:</span> {job.weight_g} g</div>
                  )}
                  {typeof job.time_hours === 'number' && (
                    <div className="text-gray-700"><span className="text-gray-500">Time:</span> {job.time_hours} h</div>
                  )}
                  {typeof job.cost_usd === 'number' && (
                    <div className="text-gray-700"><span className="text-gray-500">Cost:</span> ${job.cost_usd.toFixed(2)}</div>
                  )}
                </div>
              </div>
            )}
            {jobNotes && !isEditingNotes && (
              <div className="mt-3">
                <span className="text-gray-500 text-sm">Notes:</span>
                <div className="bg-gray-50 p-2 rounded border mt-1">
                  <p className="whitespace-pre-wrap text-sm text-gray-900">{jobNotes}</p>
                </div>
              </div>
            )}
            {isEditingNotes && (
              <div className="mt-3">
                <label htmlFor={`notes-${job.id}`} className="text-gray-500 text-sm block mb-1">Notes</label>
                <textarea
                  id={`notes-${job.id}`}
                  className="w-full min-h-[100px] border rounded-lg px-3 py-2 focus-ring text-sm"
                  value={notesDraft}
                  onChange={(e) => setNotesDraft(e.target.value)}
                  aria-describedby={`notes-status-${job.id}`}
                />
                <div className="mt-1 text-xs text-gray-500">{notesDraft.length}/{MAX_NOTES_LEN}</div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2 mt-2">
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
                <div id={`notes-status-${job.id}`} className="mt-2 text-sm" aria-live="polite">
                  {saveMessage && <span className="text-green-600">{saveMessage}</span>}
                  {saveError && <span className="text-red-600" role="alert">{saveError}</span>}
                  {notesDraft.length > MAX_NOTES_LEN && (
                    <div className="text-red-600" role="alert">Notes must be at most {MAX_NOTES_LEN} characters.</div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        <div className="flex items-center justify-between mt-4">
          <button onClick={() => setShowMore(!showMore)} className="text-sm text-gray-500 hover:text-gray-700 focus-ring btn-transition">
            {showMore ? "Show Less" : "Show More"}
          </button>

          <div className="flex space-x-2">
            {showMore && (
              <button
                onClick={beginEditNotes}
                className="flex items-center px-3 py-1 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 focus-ring btn-transition"
                title="Edit Notes"
              >
                <FileText className="w-4 h-4 mr-1" />
                Edit Notes
              </button>
            )}
            {currentStatus === "UPLOADED" && (
              <>
                <button
                  onClick={handleApprove}
                  disabled={isApproving || isRejecting}
                  className="flex items-center px-3 py-1 bg-green-100 text-green-700 rounded-lg hover:bg-green-200 disabled:opacity-50 focus-ring btn-transition"
                >
                  {isApproving ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-2 border-green-600 border-t-transparent mr-1"></div>
                      Approving...
                    </>
                  ) : (
                    <>
                      <CheckCircle className="w-4 h-4 mr-1" />
                      Approve
                    </>
                  )}
                </button>
                <button
                  onClick={handleReject}
                  disabled={isRejecting || isApproving}
                  className="flex items-center px-3 py-1 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 disabled:opacity-50 focus-ring btn-transition"
                >
                  {isRejecting ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-2 border-red-600 border-t-transparent mr-1"></div>
                      Rejecting...
                    </>
                  ) : (
                    <>
                      <XCircle className="w-4 h-4 mr-1" />
                      Reject
                    </>
                  )}
                </button>
                {!!job.staff_viewed_at && (
                  <button
                    onClick={handleReapplyNew}
                    title="Mark as Unreviewed"
                    aria-label="Mark as Unreviewed"
                    className="p-2 rounded-full bg-yellow-50 text-yellow-600 hover:bg-yellow-100 hover:text-yellow-700 focus-ring btn-transition"
                  >
                    <Eye className="w-4 h-4" />
                  </button>
                )}
              </>
            )}
            {currentStatus === "READYTOPRINT" && (
              <button
                onClick={() => onStatusAction?.(job.id, "mark-printing")}
                className="flex items-center px-3 py-1 bg-purple-100 text-purple-700 rounded-lg hover:bg-purple-200 focus-ring btn-transition"
              >
                <Printer className="w-4 h-4 mr-1" />
                Mark Printing
              </button>
            )}
            {currentStatus === "PRINTING" && (
              <button
                onClick={() => onStatusAction?.(job.id, "mark-complete")}
                className="flex items-center px-3 py-1 bg-green-100 text-green-700 rounded-lg hover:bg-green-200 focus-ring btn-transition"
              >
                <CheckCircle className="w-4 h-4 mr-1" />
                Mark Complete
              </button>
            )}
            {currentStatus === "COMPLETED" && (
              <button
                onClick={() => onStatusAction?.(job.id, "mark-picked-up")}
                className="flex items-center px-3 py-1 bg-green-100 text-green-700 rounded-lg hover:bg-green-200 focus-ring btn-transition"
              >
                <CheckCircle className="w-4 h-4 mr-1" />
                Mark Paid/Picked Up
              </button>
            )}
          </div>
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
            onMarkReviewed?.(job.id);
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
    </div>
  );
}