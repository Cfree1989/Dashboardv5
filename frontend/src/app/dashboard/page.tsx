'use client';
import React, { useState, useEffect, useCallback } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import JobList from '../../components/dashboard/job-list';
import { StatusTabs } from '../../components/dashboard/status-tabs';
import { LastUpdated } from '../../components/dashboard/last-updated';
import { DiagPanel } from '../../components/dashboard/diag-panel';
import { apiRequest, logout, getLegacyToken } from '../../lib/auth';
import { playNewUploadSound } from '../../lib/sound-utils';

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
  const [searchValue, setSearchValue] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(searchValue), 400);
    return () => clearTimeout(timer);
  }, [searchValue]);

  // Check authentication on mount
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const token = getLegacyToken();
        if (!token) {
          router.push('/login');
          return;
        }
      } catch {
        router.push('/login');
      }
    };
    checkAuth();
  }, [router]);

  // Recompute counts immediately when search changes
  useEffect(() => {
    fetchCounts();
  }, [debouncedSearch]);

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

  const handleLogout = async () => {
    await logout();
    router.push('/login');
  };

  const fetchCounts = useCallback(async () => {
    try {
      const data = await apiRequest<Record<string, number>>('/api/v1/jobs/counts');
      setCounts(data);
      
      // Play sound if UPLOADED count increased (new job submitted)
      const currentUploaded = data.UPLOADED || 0;
      const previousUploaded = counts.UPLOADED || 0;
      if (currentUploaded > previousUploaded && !pauseRefresh) {
        playNewUploadSound();
      }
    } catch (err) {
      console.error('Failed to fetch counts:', err);
    }
  }, [counts, pauseRefresh]);

  // Initial load
  useEffect(() => {
    const loadInitial = async () => {
      setLoading(true);
      await fetchCounts();
      setLoading(false);
    };
    loadInitial();
  }, [fetchCounts]);

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
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold text-gray-900">3D Print Dashboard</h1>
          <div className="flex items-center space-x-4">
            <LastUpdated lastUpdated={lastUpdated} />
            <button
              onClick={handleLogout}
              className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700 transition-colors"
            >
              Logout
            </button>
          </div>
        </div>

        <StatusTabs
          currentStatus={status}
          stats={counts}
          onStatusChange={updateStatus}
        />

        <JobList
          filters={{
            status,
            search: debouncedSearch,
          }}
          onJobsMutated={fetchCounts}
          refreshToken={refreshTick}
          onModalOpenChange={setPauseRefresh}
          searchValue={searchValue}
          onSearchInput={setSearchValue}
        />

        <DiagPanel />
      </div>
    </div>
  );
}