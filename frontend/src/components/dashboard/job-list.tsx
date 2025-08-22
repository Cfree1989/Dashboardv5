'use client';
import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import JobCard from './job-card';
import { apiRequest } from '../../lib/auth';
import { handleApiError } from '../../lib/error-handling';
import { optimizedApi } from '../../lib/optimized-api';
import { ChevronUp, ChevronDown, X } from 'lucide-react';
import { ErrorBoundary } from '../error-boundary';
import { createErrorState, updateErrorState, clearErrorState } from '../../lib/error-handling';
import { ErrorCard } from '../ui/error-display';

export interface JobListFilters {
  status?: string;
  search?: string;
  printer?: string;
  discipline?: string;
}

// Consolidated state interface
interface JobListState {
  data: {
    jobs: any[];
    hasLoaded: boolean;
  };
  loading: {
    loading: boolean;
    isFetching: boolean;
  };
  error: ReturnType<typeof createErrorState>;
  sorting: {
    sortBy: string;
    sortDir: 'asc' | 'desc';
  };
}

export default function JobList({ filters, onJobsMutated, refreshToken, onModalOpenChange, searchValue, onSearchInput, setIsJobOperation, expandSignal, collapseSignal, onToggleExpandCollapse }: { 
  filters?: JobListFilters, 
  onJobsMutated?: () => void, 
  refreshToken?: number, 
  onModalOpenChange?: (open: boolean) => void, 
  searchValue?: string, 
  onSearchInput?: (value: string) => void,
  setIsJobOperation?: (value: boolean) => void,
  expandSignal?: number,
  collapseSignal?: number,
  onToggleExpandCollapse?: () => void
}) {
  // Consolidated state management
  const [state, setState] = useState<JobListState>({
    data: {
      jobs: [],
      hasLoaded: false,
    },
    loading: {
      loading: true,
      isFetching: false,
    },
    error: createErrorState(),
    sorting: {
      sortBy: 'created_at',
      sortDir: 'desc',
    },
  });

  const router = useRouter();
  const controllerRef = useRef<AbortController | null>(null);

  // Memoized sorted jobs for better performance
  const sortedJobs = useMemo(() => {
    const copy = [...state.data.jobs];
    copy.sort((a, b) => {
      let aVal = a[state.sorting.sortBy];
      let bVal = b[state.sorting.sortBy];
      
      // Handle null/undefined values
      if (aVal == null) aVal = '';
      if (bVal == null) bVal = '';
      
      // Handle dates
      if (state.sorting.sortBy === 'created_at') {
        aVal = new Date(aVal).getTime();
        bVal = new Date(bVal).getTime();
      }
      
      // Handle strings (case-insensitive)
      if (typeof aVal === 'string') aVal = aVal.toLowerCase();
      if (typeof bVal === 'string') bVal = bVal.toLowerCase();
      
      if (aVal < bVal) return state.sorting.sortDir === 'asc' ? -1 : 1;
      if (aVal > bVal) return state.sorting.sortDir === 'asc' ? 1 : -1;
      
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
  }, [state.data.jobs, state.sorting.sortBy, state.sorting.sortDir]);

  // Memoized fetch jobs function
  const fetchJobs = useCallback(async () => {
    // cancel any in-flight
    if (controllerRef.current) {
      controllerRef.current.abort();
    }
    const controller = new AbortController();
    controllerRef.current = controller;

    if (state.data.hasLoaded) {
      setState(prev => ({ ...prev, loading: { ...prev.loading, isFetching: true } }));
    } else {
      setState(prev => ({ ...prev, loading: { ...prev.loading, loading: true } }));
    }
    setState(prev => ({ ...prev, error: clearErrorState() }));

    try {
      // Build query string based on filters
      const params = new URLSearchParams();
      if (filters?.status) params.append('status', filters.status);
      const qSearch = (filters?.search || "").trim();
      if (qSearch) params.append('search', qSearch);
      if (filters?.printer) params.append('printer', filters.printer);
      if (filters?.discipline) params.append('discipline', filters.discipline);

      const response = await optimizedApi.request<any[]>(`/api/v1/jobs?${params.toString()}`, {
        signal: controller.signal
      }, {
        ttl: 60 * 1000 // 1 minute for job lists
      });

      if (!controller.signal.aborted) {
        setState(prev => ({
          ...prev,
          data: { jobs: response, hasLoaded: true },
          loading: { loading: false, isFetching: false },
          error: clearErrorState()
        }));
      }
    } catch (err: any) {
      if (!controller.signal.aborted) {
        const newErrorState = updateErrorState(state.error, err);
        setState(prev => ({
          ...prev,
          loading: { loading: false, isFetching: false },
          error: newErrorState
        }));
      }
    }
  }, [filters?.status, filters?.search, filters?.printer, filters?.discipline, state.data.hasLoaded]);

  // Fetch jobs when filters change
  useEffect(() => {
    fetchJobs();
  }, [fetchJobs]);

  // Refresh jobs when refreshToken changes
  useEffect(() => {
    if (refreshToken && state.data.hasLoaded) {
      fetchJobs();
    }
  }, [refreshToken, fetchJobs, state.data.hasLoaded]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (controllerRef.current) {
        controllerRef.current.abort();
      }
    };
  }, []);

  // Memoized sort handler
  const handleSort = useCallback((field: string) => {
    setState(prev => ({
      ...prev,
      sorting: {
        sortBy: field,
        sortDir: prev.sorting.sortBy === field && prev.sorting.sortDir === 'asc' ? 'desc' : 'asc'
      }
    }));
  }, []);

  // Memoized job mutation handlers
  const handleJobMutation = useCallback(() => {
    if (onJobsMutated) {
      onJobsMutated();
    }
    fetchJobs();
  }, [onJobsMutated, fetchJobs]);

  const handleJobUpdate = useCallback(async (jobId: string, updates: any) => {
    try {
      await apiRequest(`/api/v1/jobs/${jobId}`, {
        method: 'PATCH',
        body: JSON.stringify(updates),
      });
      handleJobMutation();
    } catch (error) {
      throw error;
    }
  }, [handleJobMutation]);

  const handleJobDelete = useCallback(async (jobId: string) => {
    try {
      await apiRequest(`/api/v1/jobs/${jobId}`, {
        method: 'DELETE',
      });
      handleJobMutation();
    } catch (error) {
      throw error;
    }
  }, [handleJobMutation]);

  // Memoized modal open change handler
  const handleModalOpenChange = useCallback((open: boolean) => {
    if (onModalOpenChange) {
      onModalOpenChange(open);
    }
  }, [onModalOpenChange]);

  // Memoized search input handler
  const handleSearchInput = useCallback((value: string) => {
    if (onSearchInput) {
      onSearchInput(value);
    }
  }, [onSearchInput]);

  // Memoized job operation handler
  const handleSetJobOperation = useCallback((value: boolean) => {
    if (setIsJobOperation) {
      setIsJobOperation(value);
    }
  }, [setIsJobOperation]);

  if (state.loading.loading) {
    return (
      <div className="mt-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="bg-white rounded-lg shadow p-6 animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-3/4 mb-4"></div>
              <div className="h-3 bg-gray-200 rounded w-1/2 mb-2"></div>
              <div className="h-3 bg-gray-200 rounded w-2/3"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (state.error) {
    return (
      <div className="mt-8 text-center">
        <p className="text-red-600 mb-4">{state.error}</p>
        <button
          onClick={fetchJobs}
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <ErrorBoundary title="Job list error">
      <div className="mt-8">
        {/* Search and Controls */}
        <div className="mb-6 flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
          <div className="flex-1 max-w-md">
            <div className="relative">
              <input
                type="text"
                placeholder="Search jobs..."
                value={searchValue || ''}
                onChange={(e) => handleSearchInput(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              {searchValue && (
                <button
                  onClick={() => handleSearchInput('')}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center"
                >
                  <X className="h-5 w-5 text-gray-400 hover:text-gray-600" />
                </button>
              )}
            </div>
          </div>
          
          <div className="flex gap-2">
            <button
              onClick={onToggleExpandCollapse}
              className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              {(expandSignal || 0) > (collapseSignal || 0) ? (
                <>
                  <ChevronUp className="h-4 w-4" />
                  Collapse All
                </>
              ) : (
                <>
                  <ChevronDown className="h-4 w-4" />
                  Expand All
                </>
              )}
            </button>
          </div>
        </div>

        {/* Error Display */}
        {state.error.hasError && (
          <div className="mb-6">
            <ErrorCard
              error={state.error}
              onRetry={fetchJobs}
              onDismiss={() => setState(prev => ({ ...prev, error: clearErrorState() }))}
            />
          </div>
        )}

        {/* Jobs Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {sortedJobs.map((job) => (
            <JobCard
              key={job.id}
              job={job}
              currentStatus={filters?.status}
              onApprove={handleJobMutation}
              onReject={handleJobMutation}
              onMarkReviewed={handleJobMutation}
              onStatusAction={handleJobMutation}
              onUpdate={handleJobUpdate}
              onDelete={handleJobDelete}
              onModalOpenChange={handleModalOpenChange}
              expandSignal={expandSignal}
              collapseSignal={collapseSignal}
            />
          ))}
        </div>

        {sortedJobs.length === 0 && !state.loading.loading && (
          <div className="text-center py-12">
            <p className="text-gray-500 text-lg">No jobs found</p>
            {filters?.search && (
              <p className="text-gray-400 text-sm mt-2">
                Try adjusting your search criteria
              </p>
            )}
          </div>
        )}

        {state.loading.isFetching && (
          <div className="text-center py-4">
            <div className="inline-flex items-center">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></div>
              <span className="text-gray-600">Updating...</span>
            </div>
          </div>
        )}
      </div>
    </ErrorBoundary>
  );
}