"use client";
import React, { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import JobList from '../../components/dashboard/job-list';
import { SoundToggle } from '../../components/dashboard/sound-toggle';
import { LastUpdated } from '../../components/dashboard/last-updated';
import { StatusTabs } from '../../components/dashboard/status-tabs';


const statusOptions = ['UPLOADED', 'PENDING', 'READYTOPRINT', 'PRINTING', 'COMPLETED', 'PAIDPICKEDUP', 'ARCHIVED'];

export default function DashboardPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [soundOn, setSoundOn] = useState(true);
  const [lastUpdated, setLastUpdated] = useState('');
  const [isRefreshing, setIsRefreshing] = useState(false);
  useEffect(() => {
    setLastUpdated(new Date().toLocaleTimeString());
  }, []);
  const refreshPage = async () => {
    setIsRefreshing(true);
    setLastUpdated(new Date().toLocaleTimeString());
    
    // Simulate refresh delay for better UX
    await new Promise(resolve => setTimeout(resolve, 500));
    
    window.location.reload();
  };
  const logout = () => {
    localStorage.removeItem('token');
    router.push('/login');
  };
  const initialStatus = searchParams.get('status') || statusOptions[0];
  const [status, setStatus] = useState(initialStatus);
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
        const data = await res.json();
        counts[s] = (data.jobs || []).length;
      })
    );
    setStatusCounts(counts);
  };
  
  useEffect(() => {
    fetchCounts();
  }, []);
  const updateStatus = (newStatus: string) => {
    setStatus(newStatus);
    const params = new URLSearchParams();
    params.set('status', newStatus);
    router.replace(`${window.location.pathname}?${params.toString()}`);
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex flex-col md:flex-row md:items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-4 md:mb-0">3D Print Job Dashboard</h1>
        <div className="flex items-center space-x-4">
          <SoundToggle soundEnabled={soundOn} onToggle={() => setSoundOn(!soundOn)} />
          <LastUpdated lastUpdated={lastUpdated} />
          <button 
            onClick={refreshPage} 
            disabled={isRefreshing}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center focus-ring btn-transition"
          >
            {isRefreshing ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent mr-2"></div>
                Refreshing...
              </>
            ) : (
              'Refresh'
            )}
          </button>
          <button 
            onClick={logout} 
            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 focus-ring btn-transition"
          >
            Logout
          </button>
        </div>
      </div>

      <StatusTabs 
        currentStatus={status} 
        onStatusChange={updateStatus} 
        stats={statusCounts} 
      />
      <JobList filters={{ status }} />
    </div>
  );
}