"use client";
import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import JobCard from './job-card.tsx';
import ApprovalModal from './modals/approval-modal';
import StatusChangeModal from './modals/status-change-modal';
import PaymentModal from './modals/payment-modal';
import { JobListSkeleton } from './job-card-skeleton';

interface Job {
  id: string;
  display_name: string;
  student_name?: string;
  student_email?: string;
  original_filename?: string;
  printer?: string;
  color?: string;
  material?: string;
  created_at?: string;
  notes?: string;
  staff_viewed_at?: string;
}

interface JobListFilters {
  status?: string;
  search?: string;
  printer?: string;
  discipline?: string;
}
export default function JobList({ filters, onJobsMutated, refreshToken, onModalOpenChange }: { filters?: JobListFilters, onJobsMutated?: () => void, refreshToken?: number, onModalOpenChange?: (open: boolean) => void }) {
  const router = useRouter();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [approveJobId, setApproveJobId] = useState<string | null>(null);
  const [approveJobMaterial, setApproveJobMaterial] = useState<string | null>(null);
  const [statusJobId, setStatusJobId] = useState<string | null>(null);
  const [statusAction, setStatusAction] = useState<"mark-printing" | "mark-complete" | "mark-picked-up" | null>(null);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      router.push('/login');
      return;
    }
    async function fetchJobs() {
      setLoading(true);
      setError('');
      try {
        // Build query string based on filters
        const params = new URLSearchParams();
        if (filters?.status) params.append('status', filters.status);
        if (filters?.search) params.append('search', filters.search);
        if (filters?.printer) params.append('printer', filters.printer);
        if (filters?.discipline) params.append('discipline', filters.discipline);
        const res = await fetch('/api/v1/jobs' + (params.toString() ? `?${params}` : ''), {
          headers: { 'Authorization': `Bearer ${token}` },
        });
        if (res.status === 401) {
          localStorage.removeItem('token');
          router.push('/login');
          return;
        }
        if (!res.ok) {
          throw new Error(`Failed with status ${res.status}`);
        }
        const data = await res.json();
        setJobs(Array.isArray(data) ? data : (data.jobs || []));
      } catch (err) {
        setError('Failed to load jobs');
      } finally {
        setLoading(false);
      }
    }
    fetchJobs();
  }, [filters?.status, filters?.search, filters?.printer, filters?.discipline, refreshToken]);

  const openApproveModal = (jobId: string) => {
    const job = jobs.find(j => j.id === jobId);
    setApproveJobId(jobId);
    setApproveJobMaterial(job?.material || null);
    onModalOpenChange?.(true);
  };

  const closeApproveModal = () => {
    setApproveJobId(null);
    setApproveJobMaterial(null);
    onModalOpenChange?.(false);
  };

  const handleApprovedSuccess = () => {
    if (approveJobId) {
      setJobs(prev => prev.filter(j => j.id !== approveJobId));
    }
    onJobsMutated?.();
  };

  const openStatusModal = (jobId: string, action: "mark-printing" | "mark-complete" | "mark-picked-up") => {
    setStatusJobId(jobId);
    setStatusAction(action);
    onModalOpenChange?.(true);
  };

  const closeStatusModal = () => {
    setStatusJobId(null);
    setStatusAction(null);
    onModalOpenChange?.(false);
  };

  const handleStatusSuccess = () => {
    if (statusJobId) {
      setJobs(prev => prev.filter(j => j.id !== statusJobId));
    }
    onJobsMutated?.();
  };

  const handleReject = (jobId: string) => {
    // Remove rejected job from current list
    setJobs(prev => prev.filter(j => j.id !== jobId));
    onJobsMutated?.();
  };

  const handleMarkReviewed = (jobId: string) => {
    // This callback is now used to trigger a local refresh when the modal completes.
    // We will refetch the specific job to get the authoritative staff_viewed_at.
    (async () => {
      try {
        const token = localStorage.getItem('token');
        const res = await fetch(`/api/v1/jobs/${jobId}`, { headers: { Authorization: `Bearer ${token}` } });
        if (!res.ok) return;
        const updated = await res.json();
        setJobs(prev => prev.map(j => (j.id === jobId ? { ...j, staff_viewed_at: updated.staff_viewed_at } : j)));
      } catch {
        // no-op; UI will correct on next list refresh
      }
    })();
  };

  if (loading) return <JobListSkeleton />;
  
  if (error) return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center">
      <p className="text-red-600">{error}</p>
    </div>
  );
  
  if (jobs.length === 0) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center">
        <p className="text-gray-500">No jobs found for this status.</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {jobs.map(job => (
        <JobCard 
          key={job.id} 
          job={job} 
          currentStatus={filters?.status}
          onApprove={openApproveModal}
          onReject={handleReject}
          onMarkReviewed={handleMarkReviewed}
          onStatusAction={openStatusModal}
        />
      ))}
      {approveJobId && (
        <ApprovalModal
          jobId={approveJobId}
          material={approveJobMaterial || undefined}
          onClose={closeApproveModal}
          onApproved={handleApprovedSuccess}
        />
      )}
      {statusJobId && statusAction === 'mark-picked-up' && (
        <PaymentModal
          jobId={statusJobId}
          onClose={closeStatusModal}
          onSuccess={handleStatusSuccess}
        />
      )}
      {statusJobId && statusAction && statusAction !== 'mark-picked-up' && (
        <StatusChangeModal
          jobId={statusJobId}
          action={statusAction}
          title={
            statusAction === 'mark-printing' ? 'Mark as Printing' :
            statusAction === 'mark-complete' ? 'Mark as Complete' :
            'Mark as Paid/Picked Up'
          }
          description={
            statusAction === 'mark-printing' ? 'This will move the job into Printing.' : 'This will move the job to Completed.'
          }
          confirmVerb={
            statusAction === 'mark-printing' ? 'Mark Printing' : 'Mark Complete'
          }
          onClose={closeStatusModal}
          onSuccess={handleStatusSuccess}
        />
      )}
    </div>
  );
}