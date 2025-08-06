"use client";
import React, { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import JobList from '../../components/dashboard/job-list';


const statusOptions = ['UPLOADED', 'PENDING', 'READYTOPRINT', 'PRINTING', 'COMPLETED', 'PAIDPICKEDUP', 'ARCHIVED'];

export default function DashboardPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [soundOn, setSoundOn] = useState(true);
  const [lastUpdated, setLastUpdated] = useState('');
  useEffect(() => {
    setLastUpdated(new Date().toLocaleTimeString());
  }, []);
  const refreshPage = () => {
    setLastUpdated(new Date().toLocaleTimeString());
    window.location.reload();
  };
  const initialStatus = searchParams.get('status') || statusOptions[0];
  const [status, setStatus] = useState(initialStatus);
  const [statusCounts, setStatusCounts] = useState<Record<string, number>>({});
  const statusDisplayNames: Record<string, string> = {
    UPLOADED: 'Uploaded',
    PENDING: 'Pending',
    READYTOPRINT: 'Ready to Print',
    PRINTING: 'Printing',
    COMPLETED: 'Completed',
    PAIDPICKEDUP: 'Picked Up',
    ARCHIVED: 'Archived'
  };
  useEffect(() => {
    async function fetchCounts() {
      const counts: Record<string, number> = {};
      await Promise.all(
        statusOptions.map(async (s) => {
          const params = new URLSearchParams({ status: s });
          const res = await fetch('/api/v1/jobs?' + params.toString());
          const data = await res.json();
          counts[s] = (data.jobs || []).length;
        })
      );
      setStatusCounts(counts);
    }
    fetchCounts();
  }, []);
  const updateStatus = (newStatus: string) => {
    setStatus(newStatus);
    const params = new URLSearchParams();
    params.set('status', newStatus);
    router.replace(`${window.location.pathname}?${params.toString()}`);
  };

  return (
    <div>
      <header className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold">3D Print Job Dashboard</h1>
        <div className="flex items-center space-x-4">
          <button onClick={() => setSoundOn(!soundOn)} className="px-3 py-1 border rounded">
            {soundOn ? '🔊 Sound On' : '🔇 Sound Off'}
          </button>
          <span className="text-gray-600">Last updated: {lastUpdated}</span>
          <button onClick={refreshPage} className="px-3 py-1 bg-blue-600 text-white rounded">
            Refresh
          </button>
        </div>
      </header>

      <div className="my-8 flex space-x-3">
        {statusOptions.map(s => (
          <button
            key={s}
            onClick={() => updateStatus(s)}
            className={`px-6 py-3 rounded-lg text-lg font-medium flex items-center space-x-2 ${status===s ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-700'}`}
          >
            <span>{statusDisplayNames[s]}</span>
            <span className="bg-gray-300 text-gray-800 text-xs rounded-full px-2 py-0.5">{statusCounts[s] || 0}</span>
          </button>
        ))}
      </div>
      <JobList filters={{ status }} />
    </div>
  );
}