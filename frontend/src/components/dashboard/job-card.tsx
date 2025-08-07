"use client";
import React, { useState } from 'react';
import { User, Mail, Printer, Palette, FileText, CheckCircle, XCircle, Eye, RotateCcw } from "lucide-react";
import ReviewModal from './modals/review-modal';

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
}

export default function JobCard({ job, currentStatus = "UPLOADED", onApprove, onReject, onMarkReviewed }: JobCardProps) {
  const [showMore, setShowMore] = useState(false);
  const [isApproving, setIsApproving] = useState(false);
  const [isRejecting, setIsRejecting] = useState(false);
  const [isMarkingReviewed, setIsMarkingReviewed] = useState(false);
  const [showReviewModal, setShowReviewModal] = useState<null | { reviewed: boolean }>(null);
  
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
    setIsRejecting(true);
    await new Promise(resolve => setTimeout(resolve, 1000)); // Simulate API call
    onReject?.(job.id);
    setIsRejecting(false);
  };

  const handleMarkReviewed = () => {
    setShowReviewModal({ reviewed: true });
  };

  const handleReapplyNew = () => {
    setShowReviewModal({ reviewed: false });
  };

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
          <div className="flex items-center text-sm text-gray-500">
            <Printer className="w-4 h-4 mr-1" />
            <span className="truncate">{job.printer || 'Not set'}</span>
          </div>
          <div className="flex items-center text-sm text-gray-500">
            <Palette className="w-4 h-4 mr-1" />
            <span className="truncate">{job.color || 'Not set'}</span>
          </div>
        </div>

        {/* Notes indicator when collapsed */}
        {job.notes && !showMore && (
          <div className="flex items-center text-xs text-gray-500 mt-2">
            <FileText className="w-3 h-3 mr-1" />
            <span className="truncate">Has notes</span>
          </div>
        )}

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
            {job.notes && (
              <div className="mt-3">
                <span className="text-gray-500 text-sm">Notes:</span>
                <div className="bg-gray-50 p-2 rounded border mt-1">
                  <p className="whitespace-pre-wrap text-sm text-gray-900">{job.notes}</p>
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
                    className="flex items-center px-3 py-1 bg-orange-100 text-orange-700 rounded-lg hover:bg-orange-200 focus-ring btn-transition"
                  >
                    <RotateCcw className="w-4 h-4 mr-1" />
                    Reapply NEW
                  </button>
                )}
              </>
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
    </div>
  );
}