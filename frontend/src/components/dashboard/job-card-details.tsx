"use client";
import React from 'react';
import { Copy } from "lucide-react";
import { useToast } from "../ui/toast";
import { Job, JobStatus } from '../../types';

interface JobCardDetailsProps {
  job: Job;
  currentStatus: JobStatus | string;
}

export function JobCardDetails({ job, currentStatus }: JobCardDetailsProps) {
  const { show } = useToast();

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

  return (
    <div className="mt-3 pt-3 border-t border-gray-100">
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
      
      {/* Print Details (if available) */}
      {(job.weight_g || job.time_hours || job.cost_usd) && (
        <div className="mt-3">
          <h5 className="text-sm font-medium text-gray-900 mb-1">Print Details</h5>
          <div className="grid grid-cols-3 gap-2 text-sm">
            {typeof job.weight_g === 'number' && (
              <div className="text-gray-700">
                <span className="text-gray-500">
                  {currentStatus === JobStatus.PAIDPICKEDUP && job.payment ? 'Final Weight:' : 'Weight:'}
                </span>{' '}
                {currentStatus === JobStatus.PAIDPICKEDUP && job.payment ? job.payment.grams : job.weight_g} g
              </div>
            )}
            {typeof job.time_hours === 'number' && (
              <div className="text-gray-700">
                <span className="text-gray-500">Time:</span> {job.time_hours} h
              </div>
            )}
            {typeof job.cost_usd === 'number' && (
              <div className="text-gray-700">
                <span className="text-gray-500">
                  {currentStatus === JobStatus.PAIDPICKEDUP && job.payment ? 'Final Cost:' : 'Estimated Cost:'}
                </span>{' '}
                ${currentStatus === JobStatus.PAIDPICKEDUP && job.payment ? job.payment.price_usd.toFixed(2) : job.cost_usd.toFixed(2)}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
