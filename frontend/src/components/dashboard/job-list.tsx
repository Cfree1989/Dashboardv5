"use client";
import React, { useEffect, useState } from 'react';
import JobCard from './job-card.tsx';

interface Job {
  id: string;
  display_name: string;
  student_name?: string;
  student_email?: string;
  original_filename?: string;
  printer?: string;
  color?: string;
  created_at?: string;
  notes?: string;
  staff_viewed_at?: string;
}

interface JobListFilters {
  status?: string;
  search?: string;
  printer?: string;
  discipline?: string;
}
export default function JobList({ filters }: { filters?: JobListFilters }) {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    async function fetchJobs() {
      setLoading(true);
      setError('');
      try {
        // Build query string based on filters
        const params = new URLSearchParams();
        if (filters?.status) params.append('status', filters.status);
        if (filters?.search) params.append('search', filters.search);
        if (filters?.printer) params.append('printer', filters.printer);
        if (filters?.discipline) params.append('discipline', filters.discipline);
        const res = await fetch('/api/v1/jobs' + (params.toString() ? `?${params}` : ''));
        const data = await res.json();
        setJobs(data.jobs || []);
      } catch (err) {
        setError('Failed to load jobs');
      } finally {
        setLoading(false);
      }
    }
    fetchJobs();
  }, [filters.status, filters.search, filters.printer, filters.discipline]);

  if (loading) return <p>Loading jobs...</p>;
  if (error) return <p className="text-red-600">{error}</p>;
  if (jobs.length === 0) return <p>No jobs found.</p>;

  return (
    <ul className="space-y-4">
      {jobs.map(job => (
        <li key={job.id} className="bg-white shadow p-4 rounded">
          <JobCard job={job} />
        </li>
      ))}
    </ul>
  );
}