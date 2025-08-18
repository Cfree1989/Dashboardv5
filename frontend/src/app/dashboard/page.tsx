'use client';
import React, { useState, useEffect, useCallback } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import JobList from '../../components/dashboard/job-list';
import { StatusTabs } from '../../components/dashboard/status-tabs';

import { apiRequest, getLegacyToken } from '../../lib/auth';
import { playNewUploadSound } from '../../lib/sound-utils';
import { useRef } from 'react';
import { ChevronUp, ChevronDown } from 'lucide-react';

export default function DashboardPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [status, setStatus] = useState(searchParams.get('status') || 'UPLOADED');
  const [counts, setCounts] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [lastUpdated, setLastUpdated] = useState<string>('');
  const [refreshTick, setRefreshTick] = useState(0);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [pauseRefresh, setPauseRefresh] = useState(false);
  const [isJobOperation, setIsJobOperation] = useState(false);
  const [searchValue, setSearchValue] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [expandSignal, setExpandSignal] = useState(0);
  const [collapseSignal, setCollapseSignal] = useState(0);
  const [matchCounts, setMatchCounts] = useState<Record<string, number>>({});
  
  // Use ref to track previous counts for sound comparison
  const previousCountsRef = useRef<Record<string, number>>({});
  const isFirstLoadRef = useRef(true);

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(searchValue), 400);
    return () => clearTimeout(timer);
  }, [searchValue]);

  // Calculate search match counts by status
  const fetchSearchMatchCounts = useCallback(async () => {
    if (!debouncedSearch.trim()) {
      setMatchCounts({});
      return;
    }
    
    try {
      // Use the more efficient backend approach - get counts directly with search filter
      const counts = await apiRequest<Record<string, number>>('/api/v1/jobs/counts?search=' + encodeURIComponent(debouncedSearch));
      setMatchCounts(counts);
    } catch (err) {
      console.error('Failed to fetch search match counts:', err);
      setMatchCounts({});
    }
  }, [debouncedSearch]);

  const fetchCounts = useCallback(async () => {
    try {
      const data = await apiRequest<Record<string, number>>('/api/v1/jobs/counts');
      setCounts(data);
      
      // Play sound if UPLOADED count increased (new job submitted) and not due to job operations
      // Skip sound on first load to prevent playing on page refresh
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
      setIsJobOperation(false);
    } catch (err) {
      console.error('Failed to fetch counts:', err);
      setIsJobOperation(false);
    }
  }, [pauseRefresh, isJobOperation]); // Remove counts from dependencies to avoid infinite loop

  // Check authentication on mount and load initial data
  useEffect(() => {
    const checkAuthAndLoad = async () => {
      setLoading(true);
      try {
        // Test authentication by making a request to a protected endpoint
        await apiRequest('/api/v1/auth/protected');
        // If we get here, authentication is successful, so load counts
        await fetchCounts();
      } catch {
        router.push('/login');
      } finally {
        setLoading(false);
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
      setLastUpdated(ts);
      try { localStorage.setItem('lastUpdated', ts); } catch {}
      setRefreshTick((t) => t + 1);
      fetchCounts();
    }, 45000);
    return () => clearInterval(interval);
  }, [pauseRefresh, debouncedSearch]);
  
  const refreshPage = async () => {
    setIsRefreshing(true);
    const ts = new Date().toLocaleTimeString();
    setLastUpdated(ts);
    try { localStorage.setItem('lastUpdated', ts); } catch {}
    setRefreshTick((t) => t + 1);
    await fetchCounts(); // ensure tab counts update immediately
    await new Promise(resolve => setTimeout(resolve, 300));
    setIsRefreshing(false);
  };
  
  const updateStatus = (newStatus: string) => {
    setStatus(newStatus);
    const params = new URLSearchParams();
    params.set('status', newStatus);
    router.replace(`${window.location.pathname}?${params.toString()}`);
    fetchCounts(); // keep counts in sync on tab change
  };

  const toggleExpandCollapse = () => {
    // Toggle between expand and collapse modes
    if (expandSignal > collapseSignal) {
      // Currently expanded, so collapse
      setCollapseSignal(prev => prev + 1);
    } else {
      // Currently collapsed, so expand
      setExpandSignal(prev => prev + 1);
    }
  };

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
    <div className="max-w-[70%] mx-auto px-4 sm:px-6 lg:px-8 py-8">
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
  );
}