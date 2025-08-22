'use client';
import React, { useState, useEffect, useCallback, useReducer, useMemo } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import JobList from '../../components/dashboard/job-list';
import { StatusTabs } from '../../components/dashboard/status-tabs';

import { apiRequest, getLegacyToken } from '../../lib/auth';
import { playNewUploadSound } from '../../lib/sound-utils';
import { useRef } from 'react';
import { ChevronUp, ChevronDown } from 'lucide-react';
import { ErrorBoundary } from '../../components/error-boundary';

// Consolidated state types
interface DashboardState {
  // Authentication and loading
  auth: {
    loading: boolean;
    error: string;
  };
  // Search state
  search: {
    value: string;
    debounced: string;
    matchCounts: Record<string, number>;
  };
  // Refresh state
  refresh: {
    tick: number;
    isRefreshing: boolean;
    pauseRefresh: boolean;
    lastUpdated: string;
  };
  // Job operations
  jobOps: {
    isJobOperation: boolean;
    expandSignal: number;
    collapseSignal: number;
  };
  // Data state
  data: {
    status: string;
    counts: Record<string, number>;
  };
}

// Action types for useReducer
type DashboardAction =
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string }
  | { type: 'SET_SEARCH_VALUE'; payload: string }
  | { type: 'SET_DEBOUNCED_SEARCH'; payload: string }
  | { type: 'SET_MATCH_COUNTS'; payload: Record<string, number> }
  | { type: 'INCREMENT_REFRESH_TICK' }
  | { type: 'SET_REFRESHING'; payload: boolean }
  | { type: 'SET_PAUSE_REFRESH'; payload: boolean }
  | { type: 'SET_LAST_UPDATED'; payload: string }
  | { type: 'SET_JOB_OPERATION'; payload: boolean }
  | { type: 'INCREMENT_EXPAND_SIGNAL' }
  | { type: 'INCREMENT_COLLAPSE_SIGNAL' }
  | { type: 'SET_STATUS'; payload: string }
  | { type: 'SET_COUNTS'; payload: Record<string, number> };

// Initial state
const initialState: DashboardState = {
  auth: {
    loading: true,
    error: '',
  },
  search: {
    value: '',
    debounced: '',
    matchCounts: {},
  },
  refresh: {
    tick: 0,
    isRefreshing: false,
    pauseRefresh: false,
    lastUpdated: '',
  },
  jobOps: {
    isJobOperation: false,
    expandSignal: 0,
    collapseSignal: 0,
  },
  data: {
    status: 'UPLOADED',
    counts: {},
  },
};

// Reducer function
function dashboardReducer(state: DashboardState, action: DashboardAction): DashboardState {
  switch (action.type) {
    case 'SET_LOADING':
      return {
        ...state,
        auth: { ...state.auth, loading: action.payload }
      };
    case 'SET_ERROR':
      return {
        ...state,
        auth: { ...state.auth, error: action.payload }
      };
    case 'SET_SEARCH_VALUE':
      return {
        ...state,
        search: { ...state.search, value: action.payload }
      };
    case 'SET_DEBOUNCED_SEARCH':
      return {
        ...state,
        search: { ...state.search, debounced: action.payload }
      };
    case 'SET_MATCH_COUNTS':
      return {
        ...state,
        search: { ...state.search, matchCounts: action.payload }
      };
    case 'INCREMENT_REFRESH_TICK':
      return {
        ...state,
        refresh: { ...state.refresh, tick: state.refresh.tick + 1 }
      };
    case 'SET_REFRESHING':
      return {
        ...state,
        refresh: { ...state.refresh, isRefreshing: action.payload }
      };
    case 'SET_PAUSE_REFRESH':
      return {
        ...state,
        refresh: { ...state.refresh, pauseRefresh: action.payload }
      };
    case 'SET_LAST_UPDATED':
      return {
        ...state,
        refresh: { ...state.refresh, lastUpdated: action.payload }
      };
    case 'SET_JOB_OPERATION':
      return {
        ...state,
        jobOps: { ...state.jobOps, isJobOperation: action.payload }
      };
    case 'INCREMENT_EXPAND_SIGNAL':
      return {
        ...state,
        jobOps: { ...state.jobOps, expandSignal: state.jobOps.expandSignal + 1 }
      };
    case 'INCREMENT_COLLAPSE_SIGNAL':
      return {
        ...state,
        jobOps: { ...state.jobOps, collapseSignal: state.jobOps.collapseSignal + 1 }
      };
    case 'SET_STATUS':
      return {
        ...state,
        data: { ...state.data, status: action.payload }
      };
    case 'SET_COUNTS':
      return {
        ...state,
        data: { ...state.data, counts: action.payload }
      };
    default:
      return state;
  }
}

export default function DashboardPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  
  // Use reducer for consolidated state management
  const [state, dispatch] = useReducer(dashboardReducer, {
    ...initialState,
    data: {
      ...initialState.data,
      status: searchParams.get('status') || 'UPLOADED',
    }
  });
  
  // Use ref to track previous counts for sound comparison
  const previousCountsRef = useRef<Record<string, number>>({});
  const isFirstLoadRef = useRef(true);

  // Memoized selectors for better performance
  const { loading, error } = state.auth;
  const { value: searchValue, debounced: debouncedSearch, matchCounts } = state.search;
  const { tick: refreshTick, isRefreshing, pauseRefresh, lastUpdated } = state.refresh;
  const { isJobOperation, expandSignal, collapseSignal } = state.jobOps;
  const { status, counts } = state.data;

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => {
      dispatch({ type: 'SET_DEBOUNCED_SEARCH', payload: searchValue });
    }, 400);
    return () => clearTimeout(timer);
  }, [searchValue]);

  // Calculate search match counts by status
  const fetchSearchMatchCounts = useCallback(async () => {
    if (!debouncedSearch.trim()) {
      dispatch({ type: 'SET_MATCH_COUNTS', payload: {} });
      return;
    }
    
    try {
      const counts = await apiRequest<Record<string, number>>('/api/v1/jobs/counts?search=' + encodeURIComponent(debouncedSearch));
      dispatch({ type: 'SET_MATCH_COUNTS', payload: counts });
    } catch (err) {
      // Silently handle search match count failures
      dispatch({ type: 'SET_MATCH_COUNTS', payload: {} });
    }
  }, [debouncedSearch]);

  const fetchCounts = useCallback(async () => {
    try {
      const data = await apiRequest<Record<string, number>>('/api/v1/jobs/counts');
      dispatch({ type: 'SET_COUNTS', payload: data });
      
      // Play sound if UPLOADED count increased (new job submitted) and not due to job operations
      const currentUploaded = data.UPLOADED || 0;
      const previousUploaded = previousCountsRef.current.UPLOADED || 0;
      if (currentUploaded > previousUploaded && !pauseRefresh && !isJobOperation && !isFirstLoadRef.current) {
        playNewUploadSound();
      }
      
      // Update ref with current data for next comparison
      previousCountsRef.current = data;
      
      // Mark first load as complete
      isFirstLoadRef.current = false;
      
      // Reset job operation flag after counts update
      dispatch({ type: 'SET_JOB_OPERATION', payload: false });
    } catch (err) {
      // Silently handle count fetch failures
      dispatch({ type: 'SET_JOB_OPERATION', payload: false });
    }
  }, [pauseRefresh, isJobOperation]);

  // Check authentication on mount and load initial data
  useEffect(() => {
    const checkAuthAndLoad = async () => {
      dispatch({ type: 'SET_LOADING', payload: true });
      try {
        // Test authentication by making a request to a protected endpoint
        await apiRequest('/api/v1/auth/protected');
        // If we get here, authentication is successful, so load counts
        await fetchCounts();
      } catch {
        router.push('/login');
      } finally {
        dispatch({ type: 'SET_LOADING', payload: false });
      }
    };
    checkAuthAndLoad();
  }, [router, fetchCounts]);

  // Recompute counts when search changes
  useEffect(() => {
    if (counts && Object.keys(counts).length > 0) {
      fetchCounts();
    }
  }, [debouncedSearch, fetchCounts]);

  // Calculate search match counts when search changes
  useEffect(() => {
    fetchSearchMatchCounts();
  }, [fetchSearchMatchCounts]);

  // Auto-refresh every 45s: update counts and trigger list refresh (mute sound while searching)
  useEffect(() => {
    const interval = setInterval(() => {
      if (pauseRefresh) return;
      const ts = new Date().toLocaleTimeString();
      dispatch({ type: 'SET_LAST_UPDATED', payload: ts });
      try { localStorage.setItem('lastUpdated', ts); } catch {}
      dispatch({ type: 'INCREMENT_REFRESH_TICK' });
      fetchCounts();
    }, 45000);
    return () => clearInterval(interval);
  }, [pauseRefresh, debouncedSearch]);
  
  const refreshPage = useCallback(async () => {
    dispatch({ type: 'SET_REFRESHING', payload: true });
    const ts = new Date().toLocaleTimeString();
    dispatch({ type: 'SET_LAST_UPDATED', payload: ts });
    try { localStorage.setItem('lastUpdated', ts); } catch {}
    dispatch({ type: 'INCREMENT_REFRESH_TICK' });
    await fetchCounts(); // ensure tab counts update immediately
    await new Promise(resolve => setTimeout(resolve, 300));
    dispatch({ type: 'SET_REFRESHING', payload: false });
  }, [fetchCounts]);
  
  const updateStatus = useCallback((newStatus: string) => {
    dispatch({ type: 'SET_STATUS', payload: newStatus });
    const params = new URLSearchParams();
    params.set('status', newStatus);
    router.replace(`${window.location.pathname}?${params.toString()}`);
    fetchCounts(); // keep counts in sync on tab change
  }, [router, fetchCounts]);

  const toggleExpandCollapse = useCallback(() => {
    // Toggle between expand and collapse modes
    if (expandSignal > collapseSignal) {
      // Currently expanded, so collapse
      dispatch({ type: 'INCREMENT_COLLAPSE_SIGNAL' });
    } else {
      // Currently collapsed, so expand
      dispatch({ type: 'INCREMENT_EXPAND_SIGNAL' });
    }
  }, [expandSignal, collapseSignal]);

  const setSearchValue = useCallback((value: string) => {
    dispatch({ type: 'SET_SEARCH_VALUE', payload: value });
  }, []);

  const setPauseRefresh = useCallback((pause: boolean) => {
    dispatch({ type: 'SET_PAUSE_REFRESH', payload: pause });
  }, []);

  const setIsJobOperation = useCallback((isOperation: boolean) => {
    dispatch({ type: 'SET_JOB_OPERATION', payload: isOperation });
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
      <ErrorBoundary title="Dashboard section error">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <StatusTabs
            currentStatus={status}
            stats={counts}
            onStatusChange={updateStatus}
            matchCounts={matchCounts}
            searchActive={!!debouncedSearch}
          />

          <JobList 
              filters={{ status, search: debouncedSearch }} 
              onJobsMutated={fetchCounts}
              refreshToken={refreshTick}
              onModalOpenChange={setPauseRefresh}
              searchValue={searchValue}
              onSearchInput={setSearchValue}
              setIsJobOperation={setIsJobOperation}
              expandSignal={expandSignal}
              collapseSignal={collapseSignal}
              onToggleExpandCollapse={toggleExpandCollapse}
            />
        </div>
      </ErrorBoundary>
  );
}