'use client';
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import JobList from '../../components/dashboard/job-list';
import { StatusTabs } from '../../components/dashboard/status-tabs';

import { getLegacyToken } from '../../lib/auth';
import { apiClient } from '../../lib/unified-api-client';
import { useRef } from 'react';
import { ChevronUp, ChevronDown } from 'lucide-react';
import { ErrorBoundary } from '../../components/error-boundary';
import { JobStatus } from '../../types';
import { useAuthStore, useDashboardStore } from '../../store';

// Dashboard state is now managed globally with Zustand stores

export default function DashboardPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  
  // Global auth state
  const { loading, error, isAuthenticated, checkAuthStatus } = useAuthStore();
  
  // Global dashboard state
  const {
    // Search state
    searchValue,
    debouncedSearch,
    matchCounts,
    setSearchValue,
    setDebouncedSearch,
    setMatchCounts,
    
    // Refresh state
    refreshTick,
    isRefreshing,
    pauseRefresh,
    lastUpdated,
    incrementRefreshTick,
    setRefreshing,
    setPauseRefresh,
    setLastUpdated,
    
    // Job operations state
    isJobOperation,
    expandSignal,
    collapseSignal,
    setJobOperation,
    incrementExpandSignal,
    incrementCollapseSignal,
    
    // Data state
    currentStatus,
    counts,
    setCurrentStatus,
    setCounts,
    refreshData,
  } = useDashboardStore();
  
  // Use ref to track previous counts for sound comparison
  const previousCountsRef = useRef<Record<string, number>>({});
  const isFirstLoadRef = useRef(true);
  const autoRefreshIntervalRef = useRef<NodeJS.Timeout | null>(null);
  
  // Initialize status from URL params on mount
  useEffect(() => {
    const urlStatus = searchParams.get('status');
    if (urlStatus && urlStatus !== currentStatus) {
      setCurrentStatus(urlStatus);
    }
  }, [searchParams, currentStatus, setCurrentStatus]);

  // Use currentStatus instead of status
  const status = currentStatus;


  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchValue);
    }, 400);
    return () => clearTimeout(timer);
  }, [searchValue, setDebouncedSearch]);

  // Calculate search match counts by status
  const fetchSearchMatchCounts = useCallback(async () => {
    if (!debouncedSearch.trim()) {
      setMatchCounts({});
      return;
    }
    
    try {
      const counts = await apiClient.request<Record<string, number>>(
        '/api/v1/jobs/counts?search=' + encodeURIComponent(debouncedSearch),
        {},
        { ttl: 30 * 1000 } // 30 seconds for search results
      );
      setMatchCounts(counts);
    } catch (err) {
      // Silently handle search match count failures
      setMatchCounts({});
    }
  }, [debouncedSearch]);

  const fetchCounts = useCallback(async (bypass = false) => {
    try {
      const data = await apiClient.request<Record<string, number>>(
        '/api/v1/jobs/counts',
        {},
        { 
          ttl: bypass ? 0 : 30 * 1000, // allow cache bypass after mutations
          polling: {
            enabled: true,
            interval: 45000, // 45 seconds
            maxInterval: 300000, // 5 minutes max
            backoffMultiplier: 1.5,
            activityThreshold: 300000 // 5 minutes
          }
        }
      );
      
      setCounts(data);
      
      // Play sound if UPLOADED count increased (new job submitted)
      const currentUploaded = data[JobStatus.UPLOADED] || 0;
      const previousUploaded = previousCountsRef.current[JobStatus.UPLOADED] || 0;
      
      // Update ref with current data for next comparison
      previousCountsRef.current = data;
      
      // Mark first load as complete
      isFirstLoadRef.current = false;
      
      // Reset job operation flag after counts update
      setJobOperation(false);
    } catch (err) {
      // Silently handle count fetch failures
      setJobOperation(false);
    }
  }, [pauseRefresh, isJobOperation, setCounts, setJobOperation]);

  // Check authentication on mount and load initial data
  useEffect(() => {
    const checkAuthAndLoad = async () => {
      try {
        await checkAuthStatus();
        // Auth status is now managed globally, check if authenticated
        const currentState = useAuthStore.getState();
        if (currentState.isAuthenticated) {
          await fetchCounts();
        } else {
          router.push('/login');
        }
      } catch {
        router.push('/login');
      }
    };
    checkAuthAndLoad();
  }, [router, fetchCounts, checkAuthStatus]);

  // Add reliable auto-refresh mechanism
  useEffect(() => {
    // Clear any existing interval
    if (autoRefreshIntervalRef.current) {
      clearInterval(autoRefreshIntervalRef.current);
    }

    // Start auto-refresh every 30 seconds
    autoRefreshIntervalRef.current = setInterval(() => {
      if (isAuthenticated && !pauseRefresh) {
        // Fetch counts first, then trigger job list refresh
        fetchCounts().then(() => {
          // Small delay to ensure counts are processed before job list refresh
          setTimeout(() => {
            console.log(`⏲️ [DASH-REFRESH] ${new Date().toLocaleTimeString()} auto interval tick -> incrementRefreshTick()`);
            incrementRefreshTick();
          }, 500); // Half second delay to ensure proper sequencing
        });
      }
    }, 30000);

    // Cleanup on unmount
    return () => {
      if (autoRefreshIntervalRef.current) {
        clearInterval(autoRefreshIntervalRef.current);
      }
    };
  }, [isAuthenticated, pauseRefresh, fetchCounts]);

  // Props tracking for JobList updates
  useEffect(() => {
    // Dashboard props updated
  }, [refreshTick, status, debouncedSearch]);

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

  // Intelligent polling is now handled by apiClient
  // Manual interval removed in favor of adaptive polling
  
  const refreshPage = useCallback(async () => {
    setRefreshing(true);
    const ts = new Date().toLocaleTimeString();
    setLastUpdated(ts);
    try { localStorage.setItem('lastUpdated', ts); } catch {}
    console.log(`🔄 [DASH-REFRESH] ${new Date().toLocaleTimeString()} manual refresh -> incrementRefreshTick()`);
    incrementRefreshTick();
    await fetchCounts(); // ensure tab counts update immediately
    await new Promise(resolve => setTimeout(resolve, 300));
    setRefreshing(false);
  }, [fetchCounts, setRefreshing, setLastUpdated, incrementRefreshTick]);
  
  const updateStatus = useCallback((newStatus: string) => {
    setCurrentStatus(newStatus);
    const params = new URLSearchParams();
    params.set('status', newStatus);
    router.replace(`${window.location.pathname}?${params.toString()}`);
    fetchCounts(); // keep counts in sync on tab change
  }, [router, fetchCounts, setCurrentStatus]);

  const toggleExpandCollapse = useCallback(() => {
    // Toggle between expand and collapse modes
    if (expandSignal > collapseSignal) {
      // Currently expanded, so collapse
      incrementCollapseSignal();
    } else {
      // Currently collapsed, so expand
      incrementExpandSignal();
    }
  }, [expandSignal, collapseSignal, incrementCollapseSignal, incrementExpandSignal]);

  const setSearchInput = useCallback((value: string) => {
    setSearchValue(value);
  }, [setSearchValue]);

  const setPauseRefreshState = useCallback((pause: boolean) => {
    setPauseRefresh(pause);
  }, [setPauseRefresh]);

  const setIsJobOperation = useCallback((isOperation: boolean) => {
    setJobOperation(isOperation);
  }, [setJobOperation]);

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
              onJobsMutated={() => fetchCounts(true)}
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