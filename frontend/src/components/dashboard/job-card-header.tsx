"use client";
import React from 'react';
import { Mail, Printer, Palette, FileText, Eye, EyeOff } from "lucide-react";
import { TooltipProvider, Tooltip, TooltipTrigger, TooltipContent } from "../ui/tooltip";
import { Job, JobStatus } from '../../types';

interface JobCardHeaderProps {
  job: Job;
  currentStatus: JobStatus | string;
  isUnreviewed: boolean;
  isLocked: boolean;
  jobNotes: string;
  isMarkingReviewed: boolean;
  onMarkReviewed: () => void;
  onReapplyNew: () => void;
  onExpandAndEditNotes: () => void;
}

export function JobCardHeader({ 
  job, 
  currentStatus, 
  isUnreviewed, 
  isLocked,
  jobNotes,
  isMarkingReviewed,
  onMarkReviewed, 
  onReapplyNew,
  onExpandAndEditNotes 
}: JobCardHeaderProps) {
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

  return (
    <TooltipProvider>
      {/* Lock indicator */}
      {isLocked && (
        <div className="mb-2 text-sm text-red-600 font-medium">
          🔒 Locked by {job.locked_by}
        </div>
      )}

      {/* Top-right attention/unreviewed icon */}
      <div className="flex items-center justify-between mb-3">
        {currentStatus === JobStatus.UPLOADED && isUnreviewed ? (
          <span className="bg-orange-200 text-orange-900 text-xs font-semibold px-2 py-1 rounded-full">NEW</span>
        ) : (
          <span className="invisible select-none text-xs px-2 py-1">&nbsp;</span>
        )}
        {/* Right icon shown/controlled by parent card via CSS overlay; placeholder here for spacing */}
      </div>

      {/* Job title and age */}
      <div className="flex justify-between items-start mb-3">
        <h3 className="text-lg font-semibold text-gray-900 truncate">
          {job.student_name || job.display_name || (job.short_id || job.id?.slice(0,8) + '…')}
        </h3>
        <span className={`text-sm ${ageColor} font-medium`}>{timeElapsed}</span>
      </div>

      {/* Filename */}
      <p className="text-gray-600 text-sm mb-3 truncate">
        {job.display_name || job.original_filename || 'Unknown file'}
      </p>

      {/* Job details grid */}
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
              onClick={onExpandAndEditNotes}
              className="flex items-center text-sm text-gray-500 hover:text-gray-700 focus-ring btn-transition"
              title="Has notes — click to add or edit"
              aria-label="Has notes — click to add or edit"
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

      {/* Unreviewed button for already reviewed jobs */}
      {currentStatus === JobStatus.UPLOADED && !!job.staff_viewed_at && (
        <div className="mb-3">
          <Tooltip>
            <TooltipTrigger asChild>
              <button
                onClick={onReapplyNew}
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
        </div>
      )}
    </TooltipProvider>
  );
}
