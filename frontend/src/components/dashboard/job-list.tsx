'use client';
import React, { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import JobCard from './job-card';
import { apiRequest } from '../../lib/auth';

export interface JobListFilters {
  status?: string;
  search?: string;
  printer?: string;
  discipline?: string;
}

export default function JobList({ filters, onJobsMutated, refreshToken, onModalOpenChange, searchValue, onSearchInput, setIsJobOperation }: { 
  filters?: JobListFilters, 
  onJobsMutated?: () => void, 
  refreshToken?: number, 
  onModalOpenChange?: (open: boolean) => void, 
  searchValue?: string, 
  onSearchInput?: (value: string) => void,
  setIsJobOperation?: (value: boolean) => void
}) {
  const [jobs, setJobs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [isFetching, setIsFetching] = useState(false);
  const [error, setError] = useState('');
  const [hasLoaded, setHasLoaded] = useState(false);
  const [sortBy, setSortBy] = useState<string>('created_at');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');
  const router = useRouter();
  const controllerRef = useRef<AbortController | null>(null);

  const sortedJobs = () => {
    const copy = [...jobs];
    copy.sort((a, b) => {
      let aVal = a[sortBy];
      let bVal = b[sortBy];
      
      // Handle null/undefined values
      if (aVal == null) aVal = '';
      if (bVal == null) bVal = '';
      
      // Handle dates
      if (sortBy === 'created_at') {
        aVal = new Date(aVal).getTime();
        bVal = new Date(bVal).getTime();
      }
      
      // Handle strings (case-insensitive)
      if (typeof aVal === 'string') aVal = aVal.toLowerCase();
      if (typeof bVal === 'string') bVal = bVal.toLowerCase();
      
      if (aVal < bVal) return sortDir === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortDir === 'asc' ? 1 : -1;
      
      // Tie-breakers for stable sorting
      if (a.created_at !== b.created_at) {
        const aTime = new Date(a.created_at).getTime();
        const bTime = new Date(b.created_at).getTime();
        return aTime - bTime;
      }
      if (a.student_name !== b.student_name) {
        return (a.student_name || '').localeCompare(b.student_name || '');
      }
      if (a.printer !== b.printer) {
        return (a.printer || '').localeCompare(b.printer || '');
      }
      return (a.id || 0) - (b.id || 0);
    });
    return copy;
  };

  useEffect(() => {
    // cancel any in-flight
    if (controllerRef.current) {
      controllerRef.current.abort();
    }
    const controller = new AbortController();
    controllerRef.current = controller;

    async function fetchJobs() {
      if (hasLoaded) {
        setIsFetching(true);
      } else {
        setLoading(true);
      }
      setError('');
      try {
        // Build query string based on filters
        const params = new URLSearchParams();
        if (filters?.status) params.append('status', filters.status);
        const qSearch = (filters?.search || "").trim();
        if (qSearch) params.append('search', qSearch);
        if (filters?.printer) params.append('printer', filters.printer);
        if (filters?.discipline) params.append('discipline', filters.discipline);
        
        const data = await apiRequest<any>(`/api/v1/jobs${params.toString() ? `?${params}` : ''}`);
        setJobs(Array.isArray(data) ? data : (data.jobs || []));
        setHasLoaded(true);
      } catch (err: any) {
        if (err?.name === 'AbortError') {
          return; // ignore aborted
        }
        setError('Failed to load jobs');
      } finally {
        if (controllerRef.current === controller) {
          setLoading(false);
          setIsFetching(false);
        }
      }
    }
    fetchJobs();
    return () => {
      if (controllerRef.current === controller) {
        controllerRef.current.abort();
      }
    };
  }, [filters?.status, filters?.search, filters?.printer, filters?.discipline, refreshToken, router, hasLoaded]);

  const handleJobUpdate = async (jobId: string, updates: any) => {
    try {
      await apiRequest(`/api/v1/jobs/${jobId}`, {
        method: 'PATCH',
        body: JSON.stringify(updates),
      });
      
      // Update local state
      setJobs(prevJobs => 
        prevJobs.map(job => 
          job.id === jobId ? { ...job, ...updates } : job
        )
      );
      
      setIsJobOperation?.(true);
      onJobsMutated?.();
    } catch (error) {
      console.error('Failed to update job:', error);
      throw error;
    }
  };

  const handleJobDelete = async (jobId: string) => {
    try {
      await apiRequest(`/api/v1/jobs/${jobId}`, {
        method: 'DELETE',
      });
      
      // Remove from local state
      setJobs(prevJobs => prevJobs.filter(job => job.id !== jobId));
      
      setIsJobOperation?.(true);
      onJobsMutated?.();
    } catch (error) {
      console.error('Failed to delete job:', error);
      throw error;
    }
  };

  const handleJobApprove = async (jobId: string) => {
    try {
      // Remove from local state (job will move to PENDING status)
      setJobs(prevJobs => prevJobs.filter(job => job.id !== jobId));
      
      setIsJobOperation?.(true);
      onJobsMutated?.();
    } catch (error) {
      console.error('Failed to approve job:', error);
      throw error;
    }
  };

  const handleJobReject = async (jobId: string) => {
    try {
      // Remove from local state (job will move to REJECTED status)
      setJobs(prevJobs => prevJobs.filter(job => job.id !== jobId));
      
      setIsJobOperation?.(true);
      onJobsMutated?.();
    } catch (error) {
      console.error('Failed to reject job:', error);
      throw error;
    }
  };

  const handleJobMarkReviewed = async (jobId: string, updatedJob?: any) => {
    try {
      // Update job in local state using the data returned from the API
      setJobs(prevJobs => prevJobs.map(job => 
        job.id === jobId 
          ? { ...job, ...updatedJob } 
          : job
      ));
      
      setIsJobOperation?.(true);
      onJobsMutated?.();
    } catch (error) {
      console.error('Failed to mark job as reviewed:', error);
      throw error;
    }
  };

  const handleSort = (field: string) => {
    if (sortBy === field) {
      setSortDir(sortDir === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortDir('desc');
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8">
        <p className="text-red-600 mb-4">{error}</p>
        <button
          onClick={() => window.location.reload()}
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
        >
          Retry
        </button>
      </div>
    );
  }

  const sortedJobList = sortedJobs();

  return (
    <div className="space-y-4">
      {/* Search and Sort Controls */}
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        {/* Search Input */}
        <div className="flex-1 max-w-md">
          <input
            type="text"
            placeholder="Search jobs..."
            value={searchValue || ''}
            onChange={(e) => onSearchInput?.(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        {/* Sort Controls */}
        <div className="flex items-center gap-2">
          <select
            value={`${sortBy}-${sortDir}`}
            onChange={(e) => {
              const [field, dir] = e.target.value.split('-');
              setSortBy(field);
              setSortDir(dir as 'asc' | 'desc');
            }}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="created_at-desc">Time (Newest)</option>
            <option value="created_at-asc">Time (Oldest)</option>
            <option value="student_name-asc">Name (A→Z)</option>
            <option value="student_name-desc">Name (Z→A)</option>
            <option value="printer-asc">Printer (A→Z)</option>
            <option value="printer-desc">Printer (Z→A)</option>
            <option value="color-asc">Color (A→Z)</option>
            <option value="color-desc">Color (Z→A)</option>
            <option value="discipline-asc">Class (A→Z)</option>
            <option value="discipline-desc">Class (Z→A)</option>
          </select>
        </div>
      </div>

      {/* Job Count */}
      <div className="text-sm text-gray-600">
        {sortedJobList.length} job{sortedJobList.length !== 1 ? 's' : ''}
        {isFetching && <span className="ml-2">(refreshing...)</span>}
      </div>

      {/* Job Cards */}
      {sortedJobList.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <p>No jobs found</p>
          {filters?.search && (
            <p className="text-sm mt-2">Try adjusting your search terms</p>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {sortedJobList.map((job) => (
            <JobCard
              key={job.id}
              job={job}
              currentStatus={filters?.status || 'UPLOADED'}
              onApprove={handleJobApprove}
              onReject={handleJobReject}
              onMarkReviewed={handleJobMarkReviewed}
              onUpdate={handleJobUpdate}
              onDelete={handleJobDelete}
              onModalOpenChange={onModalOpenChange}
            />
          ))}
        </div>
      )}
    </div>
  );
}