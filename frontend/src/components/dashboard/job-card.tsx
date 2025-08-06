"use client";
import React, { useState } from 'react';

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

export default function JobCard({ job }: { job: Job }) {
  const [showMore, setShowMore] = useState(false);
  
  const getTimeAgo = (dateString?: string) => {
    if (!dateString) return 'recently';
    const date = new Date(dateString);
    const now = new Date();
    const diffInMs = now.getTime() - date.getTime();
    const diffInDays = Math.floor(diffInMs / (1000 * 60 * 60 * 24));
    
    if (diffInDays > 365) return 'over 1 year ago';
    if (diffInDays > 30) return `${Math.floor(diffInDays / 30)} months ago`;
    if (diffInDays > 1) return `${diffInDays} days ago`;
    return 'recently';
  };

  return (
    <div className="relative border border-gray-200 rounded-lg p-4 bg-white">
      {/* NEW Badge and Mark as Reviewed */}
      <div className="flex justify-between items-start mb-2">
        {!job.staff_viewed_at && (
          <span className="inline-block bg-orange-500 text-white text-xs font-bold px-2 py-1 rounded">
            NEW
          </span>
        )}
        {!job.staff_viewed_at && (
          <button className="text-gray-400 hover:text-gray-600 text-sm flex items-center">
            👁 Mark as Reviewed
          </button>
        )}
        <span className="text-red-500 text-sm ml-auto">
          {getTimeAgo(job.created_at)}
        </span>
      </div>

      {/* Student Name Title */}
      <h2 className="text-lg font-bold text-gray-900 mb-1">
        {job.student_name || job.display_name || job.id}
      </h2>

      {/* File Name */}
      <p className="text-gray-700 mb-3">{job.original_filename || 'Unknown file'}</p>

      {/* Student Info Row */}
      <div className="flex justify-between items-center mb-3">
        <div className="flex items-center text-gray-600">
          <span className="mr-1">👤</span>
          <span>{job.student_name || 'Unknown'}</span>
        </div>
        <div className="flex items-center text-gray-600">
          <span className="mr-1">📧</span>
          <span>{job.student_email || 'No email'}</span>
        </div>
      </div>

      {/* Printer and Color Row */}
      <div className="flex justify-between items-center mb-3">
        <div className="flex items-center text-gray-600">
          <span className="mr-1">🖨️</span>
          <span>{job.printer || 'Not assigned'}</span>
        </div>
        <div className="flex items-center text-gray-600">
          <span className="mr-1">🎨</span>
          <span>{job.color || 'No color'}</span>
        </div>
      </div>

      {/* Notes Indicator */}
      {job.notes && (
        <div className="mb-3">
          <span className="text-gray-600 text-sm flex items-center">
            📝 Has notes
          </span>
        </div>
      )}

      {/* Actions Row */}
      <div className="flex justify-between items-center">
        <button 
          onClick={() => setShowMore(!showMore)}
          className="text-gray-500 hover:text-gray-700 text-sm"
        >
          Show More
        </button>
        <div className="flex space-x-2">
          <button className="bg-green-100 text-green-700 hover:bg-green-200 px-3 py-1 rounded flex items-center">
            ✅ Approve
          </button>
          <button className="bg-red-100 text-red-700 hover:bg-red-200 px-3 py-1 rounded flex items-center">
            ❌ Reject
          </button>
        </div>
      </div>

      {/* Expandable Details */}
      {showMore && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="text-sm text-gray-600 space-y-1">
            <p><strong>Job ID:</strong> {job.id}</p>
            {job.notes && <p><strong>Notes:</strong> {job.notes}</p>}
            <p><strong>Submitted:</strong> {job.created_at ? new Date(job.created_at).toLocaleString() : 'Unknown'}</p>
          </div>
        </div>
      )}
    </div>
  );
}