"use client";
import React, { useState } from 'react';
import { formatDistanceToNow } from "date-fns";
import { User, Mail, Printer, Palette, FileText, CheckCircle, XCircle, Eye } from "lucide-react";

interface Job {
  id: string;
  display_name?: string;
  student_name?: string;
  student_email?: string;
  original_filename?: string;
  printer?: string;
  color?: string;
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
  
  const isUnreviewed = !job.staff_viewed_at;

  // Calculate job age and determine color
  const getAgeColor = (createdAt: string) => {
    const ageInHours = (Date.now() - new Date(createdAt).getTime()) / (1000 * 60 * 60);

    if (ageInHours < 24) return "text-green-600";
    if (ageInHours < 48) return "text-yellow-600";
    if (ageInHours < 72) return "text-orange-600";
    return "text-red-600";
  };

  const ageColor = job.created_at ? getAgeColor(job.created_at) : "text-gray-500";

  // Format time elapsed
  const timeElapsed = job.created_at ? formatDistanceToNow(new Date(job.created_at), { addSuffix: true }) : 'recently';

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

  const handleMarkReviewed = async () => {
    setIsMarkingReviewed(true);
    await new Promise(resolve => setTimeout(resolve, 500)); // Simulate API call
    onMarkReviewed?.(job.id);
    setIsMarkingReviewed(false);
  };

  return (
    <div
      className={`
      bg-white rounded-xl shadow-sm border transition-all card-hover
      ${isUnreviewed ? "border-orange-400 shadow-orange-100 animate-pulse-subtle" : "border-gray-200 hover:border-gray-300"}
    `}
    >
      <div className="p-4">
        {isUnreviewed && (
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
          <h3 className="text-lg font-semibold text-gray-900 truncate">{job.student_name || job.display_name || job.id}</h3>
          <span className={`text-sm ${ageColor} font-medium`}>{timeElapsed}</span>
        </div>

        <p className="text-gray-600 text-sm mb-3 truncate">{job.original_filename || job.display_name || 'Unknown file'}</p>

        <div className="grid grid-cols-2 gap-2 mb-3">
          <div className="flex items-center text-sm text-gray-500">
            <User className="w-4 h-4 mr-1" />
            <span className="truncate">{job.student_name || 'Unknown'}</span>
          </div>
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
                <p className="text-gray-900">{job.id}</p>
              </div>
              <div>
                <span className="text-gray-500">Created:</span>
                <p className="text-gray-900">{job.created_at ? new Date(job.created_at).toLocaleString() : 'Unknown'}</p>
              </div>
            </div>
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
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}