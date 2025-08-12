"use client";
import React, { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import JobList from '../../components/dashboard/job-list';
import { LastUpdated } from '../../components/dashboard/last-updated';
import { StatusTabs } from '../../components/dashboard/status-tabs';


const statusOptions = ['UPLOADED', 'PENDING', 'READYTOPRINT', 'PRINTING', 'COMPLETED', 'PAIDPICKEDUP', 'REJECTED', 'ARCHIVED'];

export default function DashboardPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [lastUpdated, setLastUpdated] = useState('');
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [refreshTick, setRefreshTick] = useState(0);
  const [pauseRefresh, setPauseRefresh] = useState(false);
  useEffect(() => {
    const now = new Date();
    const ts = now.toLocaleTimeString();
    setLastUpdated(ts);
    try { localStorage.setItem('lastUpdated', ts); } catch {}
  }, []);
  
  const [status, setStatus] = useState(searchParams.get('status') || statusOptions[0]);
  const [statusCounts, setStatusCounts] = useState<Record<string, number>>({});
  
  const fetchCounts = async () => {
    const token = localStorage.getItem('token');
    if (!token) return;
    const counts: Record<string, number> = {};
    await Promise.all(
      statusOptions.map(async (s) => {
        const params = new URLSearchParams({ status: s });
        const res = await fetch('/api/v1/jobs?' + params.toString(), {
          headers: { 'Authorization': `Bearer ${token}` },
        });
        if (res.status === 401) {
          localStorage.removeItem('token');
          router.push('/login');
          return;
        }
        if (!res.ok) return;
        const data = await res.json();
        counts[s] = Array.isArray(data) ? data.length : (data.jobs || []).length;
      })
    );
    setStatusCounts(counts);
  };
  
  useEffect(() => {
    fetchCounts();
  }, []);

  // Auto-refresh every 45s: update counts and trigger list refresh
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
  }, [pauseRefresh]);
  
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

  const logout = () => {
    localStorage.removeItem('token');
    router.push('/login');
  };

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header moved to global layout; keep page title hidden for a11y consistency */}
      <h1 className="sr-only">3D Print Job Dashboard</h1>

      <StatusTabs 
        currentStatus={status} 
        onStatusChange={updateStatus} 
        stats={statusCounts} 
      />
      <JobList 
        filters={{ status }} 
        onJobsMutated={fetchCounts} 
        refreshToken={refreshTick}
        onModalOpenChange={setPauseRefresh}
      />
    </div>
  );
}