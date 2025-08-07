"use client";
import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import JobCard from './job-card.tsx';
import ApprovalModal from './modals/approval-modal';
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
export default function JobList({ filters, onJobsMutated }: { filters?: JobListFilters, onJobsMutated?: () => void }) {
  const router = useRouter();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [approveJobId, setApproveJobId] = useState<string | null>(null);
  const [approveJobMaterial, setApproveJobMaterial] = useState<string | null>(null);

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
        const data = await res.json();
        setJobs(Array.isArray(data) ? data : (data.jobs || []));
      } catch (err) {
        setError('Failed to load jobs');
      } finally {
        setLoading(false);
      }
    }
    fetchJobs();
  }, [filters?.status, filters?.search, filters?.printer, filters?.discipline]);

  const openApproveModal = (jobId: string) => {
    const job = jobs.find(j => j.id === jobId);
    setApproveJobId(jobId);
    setApproveJobMaterial(job?.material || null);
  };

  const closeApproveModal = () => {
    setApproveJobId(null);
    setApproveJobMaterial(null);
  };

  const handleApprovedSuccess = () => {
    if (approveJobId) {
      setJobs(prev => prev.filter(j => j.id !== approveJobId));
    }
    onJobsMutated?.();
  };

  const handleReject = (jobId: string) => {
    console.log("Reject job:", jobId);
    // TODO: Implement rejection logic
  };

  const handleMarkReviewed = (jobId: string) => {
    console.log("Mark as reviewed:", jobId);
    // Update local state to mark as reviewed
    setJobs(prevJobs => 
      prevJobs.map(job => 
        job.id === jobId ? { ...job, staff_viewed_at: new Date().toISOString() } : job
      )
    );
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
    </div>
  );
}