'use client';
import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import JobCard from './job-card';
import { handleApiError } from '../../lib/error-handling';
import { apiClient } from '../../lib/unified-api-client';
import { ChevronUp, ChevronDown, X } from 'lucide-react';
import { ErrorBoundary } from '../error-boundary';
import { createErrorState, updateErrorState, clearErrorState } from '../../lib/error-handling';
import { ErrorCard } from '../ui/error-display';
import { JobListFilters, JobListState, Job, JobStatus } from '../../types';

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
  const [needsAttention, setNeedsAttention] = useState<boolean>(false);

  const router = useRouter();
  const controllerRef = useRef<AbortController | null>(null);

  // JobList render tracking

  // React Strict Mode compatibility: Skip cleanup in development
  useEffect(() => {
    return () => {
      // Skip cleanup in development mode to prevent React Strict Mode interference
      if (process.env.NODE_ENV === 'development') {
        return;
      }
      // Only cleanup in production
      if (controllerRef.current) {
        controllerRef.current.abort();
      }
    };
  }, []);

  // Memoized sorted jobs for better performance
  const sortedJobs = useMemo(() => {
    // Safety check: ensure jobs is an array before spreading
    if (!Array.isArray(state.data.jobs)) {
      return [];
    }
    const copy = [...state.data.jobs];
    // If viewing Uploaded, group: Unreviewed first -> Needs Attention -> others
    if ((filters?.status || '') === JobStatus.UPLOADED) {
      copy.sort((a, b) => {
        const aUn = a.is_unreviewed === true ? 1 : 0;
        const bUn = b.is_unreviewed === true ? 1 : 0;
        if (aUn !== bUn) return bUn - aUn; // unreviewed first
        const aNa = a.needs_attention === true ? 1 : 0;
        const bNa = b.needs_attention === true ? 1 : 0;
        if (aNa !== bNa) return bNa - aNa; // then attention
        return 0;
      });
    }
    copy.sort((a, b) => {
      let aVal: any = (a as any)[state.sorting.sortBy];
      let bVal: any = (b as any)[state.sorting.sortBy];
      
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
        const aTime = new Date(a.created_at || '').getTime();
        const bTime = new Date(b.created_at || '').getTime();
        return aTime - bTime;
      }
      if (a.student_name !== b.student_name) {
        return (a.student_name || '').localeCompare(b.student_name || '');
      }
      if (a.printer !== b.printer) {
        return (a.printer || '').localeCompare(b.printer || '');
      }
      return (a.id || '').localeCompare(b.id || '');
    });
    return copy;
  }, [state.data.jobs, state.sorting.sortBy, state.sorting.sortDir]);

  // Add ref to prevent concurrent fetches
  const isFetchingRef = useRef(false);
  
  // Memoized fetch jobs function
  const fetchJobs = useCallback(async (bypassCache = false) => {
    // Prevent concurrent fetches (even when bypassing cache)
    if (isFetchingRef.current) {
      console.log(`⏭️ [FETCH-JOBS-TIMING] ${new Date().toLocaleTimeString()} Skipping duplicate fetchJobs call (already fetching)`);
      return;
    }
    
    isFetchingRef.current = true;
    const fetchStartTime = Date.now();
    const cacheStatus = bypassCache ? "(BYPASSING CACHE)" : "(using cache)";
    console.log(`📡 [FETCH-JOBS-TIMING] ${new Date().toLocaleTimeString()} fetchJobs() started for status: ${filters?.status || 'ALL'} ${cacheStatus}`);
    
    // Always create a fresh controller - don't try to abort existing ones in development
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
      if (filters?.status) {
        params.append('status', filters.status);
      }
      const qSearch = (filters?.search || "").trim();
      if (qSearch) params.append('search', qSearch);
      if (filters?.printer) params.append('printer', filters.printer);
      if (filters?.discipline) params.append('discipline', filters.discipline);
      if (needsAttention) params.append('needs_attention', 'true');

      // Cache-busting when bypassing cache to avoid any intermediary caches returning stale data
      if (bypassCache) {
        params.append('_ts', String(Date.now()));
      }
      const apiUrl = `/api/v1/jobs?${params.toString()}`;
      
      const apiStartTime = Date.now();
      console.log(`🌐 [FETCH-JOBS-TIMING] ${new Date().toLocaleTimeString()} Making API request to: ${apiUrl}`);
      
      const response = await apiClient.request<any[]>(apiUrl, {
        signal: controller.signal
      }, {
        ttl: bypassCache ? 0 : (state.data.hasLoaded ? 60 * 1000 : 0) // Bypass cache when explicitly requested
      });

      const apiEndTime = Date.now();
      console.log(`📨 [FETCH-JOBS-TIMING] ${new Date().toLocaleTimeString()} API response received in ${apiEndTime - apiStartTime}ms, job count: ${response.length}`);

      if (!controller.signal.aborted) {
        const stateUpdateStart = Date.now();
        setState(prev => {
          const previousJobCount = prev.data.jobs.length;
          const newJobCount = response.length;
          const hadLoaded = prev.data.hasLoaded;
          
          console.log(`🔄 [FETCH-JOBS-TIMING] ${new Date().toLocaleTimeString()} Updating state: ${previousJobCount} -> ${newJobCount} jobs, hadLoaded: ${hadLoaded}`);
          
          return {
            ...prev,
            data: { jobs: response, hasLoaded: true },
            loading: { loading: false, isFetching: false },
            error: clearErrorState()
          };
        });
        
        const stateUpdateEnd = Date.now();
        const totalFetchTime = Date.now() - fetchStartTime;
        console.log(`🎯 [FETCH-JOBS-TIMING] ${new Date().toLocaleTimeString()} State update completed in ${stateUpdateEnd - stateUpdateStart}ms`);
        console.log(`✅ [FETCH-JOBS-TIMING] ${new Date().toLocaleTimeString()} Total fetchJobs() time: ${totalFetchTime}ms`);
      }
    } catch (err: any) {
      if (!controller.signal.aborted) {
        console.error(`❌ [FETCH-JOBS-TIMING] ${new Date().toLocaleTimeString()} fetchJobs() failed:`, err);
        const newErrorState = updateErrorState(state.error, err);
        setState(prev => ({
          ...prev,
          loading: { loading: false, isFetching: false },
          error: newErrorState
        }));
      }
    } finally {
      // Always reset fetch guard
      isFetchingRef.current = false;
    }
  }, [filters?.status, filters?.search, filters?.printer, filters?.discipline, needsAttention]);

  // Fetch jobs when filters change
  useEffect(() => {
    fetchJobs();
  }, [fetchJobs]);

  // Listen for simple mutation event to refresh list
  useEffect(() => {
    const handler = () => fetchJobs(true);
    if (typeof window !== 'undefined') {
      window.addEventListener('dashboard:jobs:mutated', handler);
    }
    return () => {
      if (typeof window !== 'undefined') {
        window.removeEventListener('dashboard:jobs:mutated', handler);
      }
    };
  }, [fetchJobs]);

  // Refresh jobs when refreshToken changes
  useEffect(() => {
    if (refreshToken && state.data.hasLoaded) {
      // Bypass cache on auto refresh to avoid stale lists after external mutations
      fetchJobs(true);
    }
  }, [refreshToken, fetchJobs, state.data.hasLoaded]);

  // Cleanup on unmount - React Strict Mode compatibility
  useEffect(() => {
    return () => {
      // Skip cleanup in development mode to prevent React Strict Mode interference  
      if (process.env.NODE_ENV === 'development') {
        return;
      }
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
  const handleJobMutation = useCallback(async (mutatedJobId?: string) => {
    const mutationStartTime = Date.now();
    console.log(`🔄 [JOB-LIST-TIMING] ${new Date().toLocaleTimeString()} handleJobMutation started`);
    
    if (onJobsMutated) {
      console.log(`📢 [JOB-LIST-TIMING] ${new Date().toLocaleTimeString()} Calling onJobsMutated() callback...`);
      onJobsMutated();
    }
    // Optimistic removal: if we are viewing a filtered list (e.g., UPLOADED) and a job has just
    // transitioned out of this status (approve/reject/etc), remove it immediately from local state
    if (mutatedJobId) {
      setState(prev => ({
        ...prev,
        data: {
          ...prev.data,
          jobs: prev.data.jobs.filter(j => j.id !== mutatedJobId)
        }
      }));
    }
    
    const fetchStartTime = Date.now();
    console.log(`📊 [JOB-LIST-TIMING] ${new Date().toLocaleTimeString()} Starting centralized fresh refetch via apiClient...`);

    try {
      // Build list URL consistent with fetchJobs
      const params = new URLSearchParams();
      if (filters?.status) params.append('status', filters.status);
      const qSearch = (filters?.search || '').trim();
      if (qSearch) params.append('search', qSearch);
      if (filters?.printer) params.append('printer', filters.printer);
      if (filters?.discipline) params.append('discipline', filters.discipline);
      if (filters?.needs_attention === true) params.append('needs_attention', 'true');
      const apiUrl = `/api/v1/jobs?${params.toString()}`;

      // Mutation already happened in modal; run a no-op mutation and refetch list fresh
      const { jobs } = await apiClient.mutateThenRefetch({
        mutation: async () => Promise.resolve(),
        listUrl: apiUrl,
        refetchCounts: false,
      });

      if (Array.isArray(jobs)) {
        setState(prev => ({
          ...prev,
          data: { jobs, hasLoaded: true },
          loading: { ...prev.loading, isFetching: false },
          error: clearErrorState(),
        }));
      } else {
        // Fallback: fetch list directly with ttl: 0 and update state
        const fresh = await apiClient.request<any[]>(apiUrl, { method: 'GET', cache: 'no-store' }, { ttl: 0 });
        setState(prev => ({
          ...prev,
          data: { jobs: fresh, hasLoaded: true },
          loading: { ...prev.loading, isFetching: false },
          error: clearErrorState(),
        }));
      }
    } catch (err) {
      console.error(`❌ [JOB-LIST-TIMING] ${new Date().toLocaleTimeString()} centralized refetch failed:`, err);
      try {
        const params = new URLSearchParams();
        if (filters?.status) params.append('status', filters.status);
        const qSearch = (filters?.search || '').trim();
        if (qSearch) params.append('search', qSearch);
        if (filters?.printer) params.append('printer', filters.printer);
        if (filters?.discipline) params.append('discipline', filters.discipline);
        const apiUrl = `/api/v1/jobs?${params.toString()}`;
        const fresh = await apiClient.request<any[]>(apiUrl, { method: 'GET', cache: 'no-store' }, { ttl: 0 });
        setState(prev => ({
          ...prev,
          data: { jobs: fresh, hasLoaded: true },
          loading: { ...prev.loading, isFetching: false },
          error: clearErrorState(),
        }));
      } catch (e) {
        // Last resort: keep existing state and surface error through existing error handling
      }
    }

    const fetchEndTime = Date.now();
    const totalTime = Date.now() - mutationStartTime;
    console.log(`✅ [JOB-LIST-TIMING] ${new Date().toLocaleTimeString()} centralized refetch completed in ${fetchEndTime - fetchStartTime}ms`);
    console.log(`⏱️ [JOB-LIST-TIMING] ${new Date().toLocaleTimeString()} Total handleJobMutation time: ${totalTime}ms`);
  }, [onJobsMutated, fetchJobs, filters?.status, filters?.search, filters?.printer, filters?.discipline]);

  const handleJobUpdate = useCallback(async (jobId: string, updates: any) => {
    try {
      await apiClient.put(`/api/v1/jobs/${jobId}`, updates);
      await handleJobMutation();
    } catch (error) {
      throw error;
    }
  }, [handleJobMutation]);

  const handleJobDelete = useCallback(async (jobId: string) => {
    try {
      await apiClient.delete(`/api/v1/jobs/${jobId}`);
      await handleJobMutation();
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

  if (state.error.hasError) {
    return (
      <div className="mt-8 text-center">
        <p className="text-red-600 mb-4">{state.error.message}</p>
        <button
          onClick={() => fetchJobs()}
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
          
          <div className="flex gap-2 items-center">
            <label className="inline-flex items-center gap-2 text-sm text-gray-700">
              <input
                type="checkbox"
                className="rounded border-gray-300 text-orange-600 focus:ring-orange-500"
                checked={needsAttention}
                onChange={(e) => {
                  setNeedsAttention(e.target.checked);
                  fetchJobs(true);
                }}
              />
              Needs Attention
            </label>
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
              onRetry={() => fetchJobs()}
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