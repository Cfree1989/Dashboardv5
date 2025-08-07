"use client";
import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
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
  const router = useRouter();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      router.push('/login');
      return;
    }
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
        const res = await fetch('/api/v1/jobs' + (params.toString() ? `?${params}` : ''), {
          headers: { 'Authorization': `Bearer ${token}` },
        });
        const data = await res.json();
        setJobs(data.jobs || []);
      } catch (err) {
        setError('Failed to load jobs');
      } finally {
        setLoading(false);
      }
    }
    fetchJobs();
  }, [filters?.status, filters?.search, filters?.printer, filters?.discipline]);

  const handleApprove = (jobId: string) => {
    console.log("Approve job:", jobId);
    // TODO: Implement approval logic
  };

  const handleReject = (jobId: string) => {
    console.log("Reject job:", jobId);
    // TODO: Implement rejection logic
  };

  const handleMarkReviewed = (jobId: string) => {
    console.log("Mark as reviewed:", jobId);
    // Update local state to mark as reviewed
    setJobs(prevJobs => 
      prevJobs.map(job => 
        job.id === jobId ? { ...job, staff_viewed_at: new Date().toISOString() } : job
      )
    );
  };

  if (loading) return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center">
      <p className="text-gray-500">Loading jobs...</p>
    </div>
  );
  
  if (error) return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center">
      <p className="text-red-600">{error}</p>
    </div>
  );
  
  if (jobs.length === 0) {
    // Show mock data when no real jobs exist
    const mockJobs: Job[] = [
      {
        id: "mock-001",
        student_name: "Alice Johnson",
        student_email: "alice.johnson@university.edu", 
        original_filename: "dragon_miniature.stl",
        display_name: "Dragon Miniature",
        printer: "Prusa MK4S",
        color: "Silver PLA",
        created_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(), // 2 hours ago
        notes: "Student requested high detail settings for this miniature",
        staff_viewed_at: undefined // NEW - will show pulsing badge
      },
      {
        id: "mock-002", 
        student_name: "Bob Chen",
        student_email: "b.chen@university.edu",
        original_filename: "phone_case_custom.stl",
        display_name: "Custom Phone Case",
        printer: "Raise3D Pro 2 Plus",
        color: "Blue PETG",
        created_at: new Date(Date.now() - 26 * 60 * 60 * 1000).toISOString(), // 26 hours ago - will be yellow
        notes: undefined,
        staff_viewed_at: new Date(Date.now() - 20 * 60 * 60 * 1000).toISOString() // reviewed
      },
      {
        id: "mock-003",
        student_name: "Carol Martinez",
        student_email: "carol.martinez@university.edu",
        original_filename: "engineering_bracket.stl", 
        display_name: "Engineering Support Bracket",
        printer: "Prusa XL",
        color: "Black PLA",
        created_at: new Date(Date.now() - 50 * 60 * 60 * 1000).toISOString(), // 50 hours ago - will be orange
        notes: "For senior capstone project - needs to be strong",
        staff_viewed_at: new Date(Date.now() - 45 * 60 * 60 * 1000).toISOString()
      },
      {
        id: "mock-004",
        student_name: "David Kumar", 
        student_email: "d.kumar@university.edu",
        original_filename: "art_sculpture.stl",
        display_name: "Abstract Art Sculpture",
        printer: "Formlabs Form 3",
        color: "Clear Resin",
        created_at: new Date(Date.now() - 80 * 60 * 60 * 1000).toISOString(), // 80 hours ago - will be red
        notes: undefined,
        staff_viewed_at: undefined // NEW - will show pulsing badge
      },
      {
        id: "mock-005",
        student_name: "Emma Wilson",
        student_email: "emma.w@university.edu", 
        original_filename: "gear_assembly.stl",
        display_name: "Mechanical Gear Assembly",
        printer: "Prusa MK4S",
        color: "White PLA",
        created_at: new Date(Date.now() - 12 * 60 * 60 * 1000).toISOString(), // 12 hours ago - will be green
        notes: "Part of robotics competition project",
        staff_viewed_at: new Date(Date.now() - 8 * 60 * 60 * 1000).toISOString()
      },
      {
        id: "mock-006",
        student_name: "Frank Rodriguez",
        student_email: "f.rodriguez@university.edu",
        original_filename: "architectural_model.stl",
        display_name: "Building Scale Model", 
        printer: "Raise3D Pro 2 Plus",
        color: "Gray PLA",
        created_at: new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString(), // 6 hours ago - will be green
        notes: undefined,
        staff_viewed_at: undefined // NEW - will show pulsing badge
      }
    ];

    return (
      <div className="space-y-4">
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 mb-4">
          <p className="text-blue-800 text-sm">
            <strong>Demo Mode:</strong> Showing mock jobs to preview the V0 dashboard design. 
            Connect to your API to see real job data.
          </p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {mockJobs.map(job => (
            <JobCard 
              key={job.id} 
              job={job} 
              currentStatus={filters?.status}
              onApprove={handleApprove}
              onReject={handleReject}
              onMarkReviewed={handleMarkReviewed}
            />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {jobs.map(job => (
        <JobCard 
          key={job.id} 
          job={job} 
          currentStatus={filters?.status}
          onApprove={handleApprove}
          onReject={handleReject}
          onMarkReviewed={handleMarkReviewed}
        />
      ))}
    </div>
  );
}