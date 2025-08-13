"use client";
import React, { useEffect, useMemo, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import JobCard from './job-card.tsx';
import ApprovalModal from './modals/approval-modal';
import StatusChangeModal from './modals/status-change-modal';
import PaymentModal from './modals/payment-modal';
import { JobListSkeleton } from './job-card-skeleton';
import { useReducedMotion } from '../../lib/use-reduced-motion';
import { ArrowUp, ArrowDown, ChevronDown, ChevronUp, Search as SearchIcon, X as XIcon } from "lucide-react";

interface Job {
  id: string;
  display_name: string;
  student_name?: string;
  student_email?: string;
  original_filename?: string;
  printer?: string;
  color?: string;
  material?: string;
  created_at?: string;
  notes?: string;
  staff_viewed_at?: string;
  class_number?: string;
}

interface JobListFilters {
  status?: string;
  search?: string;
  printer?: string;
  discipline?: string;
}
export default function JobList({ filters, onJobsMutated, refreshToken, onModalOpenChange, searchValue, onSearchInput }: { filters?: JobListFilters, onJobsMutated?: () => void, refreshToken?: number, onModalOpenChange?: (open: boolean) => void, searchValue?: string, onSearchInput?: (value: string) => void }) {
  const router = useRouter();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [approveJobId, setApproveJobId] = useState<string | null>(null);
  const [approveJobMaterial, setApproveJobMaterial] = useState<string | null>(null);
  const [approveJobPrinter, setApproveJobPrinter] = useState<string | null>(null);
  const [statusJobId, setStatusJobId] = useState<string | null>(null);
  const [statusAction, setStatusAction] = useState<"mark-printing" | "mark-complete" | "mark-picked-up" | null>(null);
  const prefersReducedMotion = useReducedMotion();

  type SortBy = 'time' | 'name' | 'printer' | 'color' | 'class';
  type SortDir = 'asc' | 'desc';
  const [sortBy, setSortBy] = useState<SortBy>('time');
  const [sortDir, setSortDir] = useState<SortDir>('desc');
  const [isFading, setIsFading] = useState(false);
  const [expandAllSignal, setExpandAllSignal] = useState(0);
  const [collapseAllSignal, setCollapseAllSignal] = useState(0);
  const [allOpen, setAllOpen] = useState(false);
  const [hasLoaded, setHasLoaded] = useState(false);
  const [isFetching, setIsFetching] = useState(false);
  const controllerRef = useRef<AbortController | null>(null);

  // Load persisted sort on mount
  useEffect(() => {
    try {
      const raw = localStorage.getItem('dashboard.sort.v1');
      if (raw) {
        const parsed = JSON.parse(raw);
        if (parsed && (parsed.sortBy === 'time' || parsed.sortBy === 'name' || parsed.sortBy === 'printer')) {
          setSortBy(parsed.sortBy);
        }
        if (parsed && (parsed.sortDir === 'asc' || parsed.sortDir === 'desc')) {
          setSortDir(parsed.sortDir);
        }
      }
    } catch {}
  }, []);

  // Persist selection and trigger a gentle fade
  useEffect(() => {
    try { localStorage.setItem('dashboard.sort.v1', JSON.stringify({ sortBy, sortDir })); } catch {}
    if (!prefersReducedMotion) {
      setIsFading(true);
      const t = setTimeout(() => setIsFading(false), 180);
      return () => clearTimeout(t);
    }
  }, [sortBy, sortDir, prefersReducedMotion]);

  // Gentle fade on sort changes only

  // Reset bulk state on status change to avoid confusion
  useEffect(() => {
    setAllOpen(false);
  }, [filters?.status]);

  function compareStrings(a?: string, b?: string): number {
    const aa = (a || '').toLowerCase();
    const bb = (b || '').toLowerCase();
    if (aa < bb) return -1;
    if (aa > bb) return 1;
    return 0;
  }

  const sortedJobs = useMemo(() => {
    const copy = [...jobs];
    copy.sort((a, b) => {
      // base comparisons
      let cmp = 0;
      if (sortBy === 'time') {
        const at = a.created_at ? new Date(a.created_at).getTime() : 0;
        const bt = b.created_at ? new Date(b.created_at).getTime() : 0;
        cmp = at === bt ? 0 : (at < bt ? -1 : 1);
      } else if (sortBy === 'name') {
        const an = a.student_name || a.display_name || '';
        const bn = b.student_name || b.display_name || '';
        cmp = compareStrings(an, bn);
      } else if (sortBy === 'printer') {
        cmp = compareStrings(a.printer, b.printer);
      } else if (sortBy === 'color') {
        cmp = compareStrings(a.color, b.color);
      } else if (sortBy === 'class') {
        cmp = compareStrings(a.class_number, b.class_number);
      }
      if (cmp === 0) {
        // Tie-breakers for stability: time desc, then name asc, then printer asc, then id asc
        const at = a.created_at ? new Date(a.created_at).getTime() : 0;
        const bt = b.created_at ? new Date(b.created_at).getTime() : 0;
        cmp = bt - at; // newer first
        if (cmp === 0) {
          cmp = compareStrings(a.student_name || a.display_name, b.student_name || b.display_name);
          if (cmp === 0) {
            cmp = compareStrings(a.printer, b.printer);
            if (cmp === 0) {
              cmp = compareStrings(a.id, b.id);
            }
          }
        }
      }
      return sortDir === 'asc' ? cmp : -cmp;
    });
    return copy;
  }, [jobs, sortBy, sortDir]);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      router.push('/login');
      return;
    }
    // cancel any in-flight
    if (controllerRef.current) {
      controllerRef.current.abort();
    }
    const controller = new AbortController();
    controllerRef.current = controller;

    async function fetchJobs() {
      if (hasLoaded) {
        setIsFetching(true);
      } else {
        setLoading(true);
      }
      setError('');
      try {
        // Build query string based on filters
        const params = new URLSearchParams();
        if (filters?.status) params.append('status', filters.status);
        const qSearch = (filters?.search || "").trim();
        if (qSearch) params.append('search', qSearch);
        if (filters?.printer) params.append('printer', filters.printer);
        if (filters?.discipline) params.append('discipline', filters.discipline);
        const res = await fetch('/api/v1/jobs' + (params.toString() ? `?${params}` : ''), {
          headers: { 'Authorization': `Bearer ${token}` },
          signal: controller.signal,
        });
        if (res.status === 401) {
          localStorage.removeItem('token');
          router.push('/login');
          return;
        }
        if (!res.ok) {
          throw new Error(`Failed with status ${res.status}`);
        }
        const data = await res.json();
        setJobs(Array.isArray(data) ? data : (data.jobs || []));
        setHasLoaded(true);
      } catch (err: any) {
        if (err?.name === 'AbortError') {
          return; // ignore aborted
        }
        setError('Failed to load jobs');
      } finally {
        if (controllerRef.current === controller) {
          setLoading(false);
          setIsFetching(false);
        }
      }
    }
    fetchJobs();
    return () => {
      if (controllerRef.current === controller) {
        controllerRef.current.abort();
      }
    };
  }, [filters?.status, filters?.search, filters?.printer, filters?.discipline, refreshToken]);

  const openApproveModal = (jobId: string) => {
    const job = jobs.find(j => j.id === jobId);
    setApproveJobId(jobId);
    setApproveJobMaterial(job?.material || null);
    setApproveJobPrinter(job?.printer || null);
    onModalOpenChange?.(true);
  };

  const closeApproveModal = () => {
    setApproveJobId(null);
    setApproveJobMaterial(null);
    setApproveJobPrinter(null);
    onModalOpenChange?.(false);
  };

  const handleApprovedSuccess = () => {
    if (approveJobId) {
      setJobs(prev => prev.filter(j => j.id !== approveJobId));
    }
    onJobsMutated?.();
  };

  const openStatusModal = (jobId: string, action: "mark-printing" | "mark-complete" | "mark-picked-up") => {
    setStatusJobId(jobId);
    setStatusAction(action);
    onModalOpenChange?.(true);
  };

  const closeStatusModal = () => {
    setStatusJobId(null);
    setStatusAction(null);
    onModalOpenChange?.(false);
  };

  const handleStatusSuccess = () => {
    if (statusJobId) {
      setJobs(prev => prev.filter(j => j.id !== statusJobId));
    }
    onJobsMutated?.();
  };

  const handleReject = (jobId: string) => {
    // Remove rejected job from current list
    setJobs(prev => prev.filter(j => j.id !== jobId));
    onJobsMutated?.();
  };

  const handleMarkReviewed = (jobId: string) => {
    // This callback is now used to trigger a local refresh when the modal completes.
    // We will refetch the specific job to get the authoritative staff_viewed_at.
    (async () => {
      try {
        const token = localStorage.getItem('token');
        const res = await fetch(`/api/v1/jobs/${jobId}`, { headers: { Authorization: `Bearer ${token}` } });
        if (!res.ok) return;
        const updated = await res.json();
        setJobs(prev => prev.map(j => (j.id === jobId ? { ...j, staff_viewed_at: updated.staff_viewed_at } : j)));
      } catch {
        // no-op; UI will correct on next list refresh
      }
    })();
  };

  if (!hasLoaded && loading) return <JobListSkeleton />;

  return (
    <div>
      {/* Search + Bulk actions + Sort controls */}
      <div className="flex items-center justify-between mb-2 gap-2">
        <div className="flex items-center gap-2">
          {/* Search input (controlled by page) */}
          <div className="relative">
            <SearchIcon className="w-4 h-4 text-gray-400 absolute left-2 top-1/2 -translate-y-1/2 pointer-events-none" />
            <input
              type="search"
              value={searchValue || ""}
              onChange={(e) => onSearchInput?.(e.target.value)}
              placeholder="Search name or email"
              className="pl-7 pr-7 py-1.5 text-sm border rounded w-48 md:w-64 focus-ring"
              aria-label="Search jobs by name or email"
            />
            {searchValue ? (
              <button
                type="button"
                className="absolute right-1 top-1/2 -translate-y-1/2 p-1 text-gray-500 hover:text-gray-700"
                aria-label="Clear search"
                onClick={() => onSearchInput?.("")}
              >
                <XIcon className="w-4 h-4" />
              </button>
            ) : null}
          </div>

          <button
            type="button"
            className="inline-flex items-center gap-1 border rounded px-2 py-1 text-sm hover:bg-gray-50 bg-white"
            onClick={() => {
              if (allOpen) {
                setCollapseAllSignal(v => v + 1);
              } else {
                setExpandAllSignal(v => v + 1);
              }
              setAllOpen(v => !v);
            }}
            aria-label={allOpen ? "Collapse all cards" : "Open all cards"}
            title={allOpen ? "Collapse all" : "Open all"}
          >
            {allOpen ? (
              <ChevronUp className="w-4 h-4" />
            ) : (
              <ChevronDown className="w-4 h-4" />
            )}
            <span className="sr-only">{allOpen ? 'Collapse all' : 'Open all'}</span>
          </button>
        </div>
        
        <div className="flex items-center gap-2">
        <label htmlFor="sortBy" className="text-sm text-gray-600">Sort by:</label>
        <select
          id="sortBy"
          className="border rounded px-2 py-1 text-sm"
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value as SortBy)}
        >
          <option value="time">Time</option>
          <option value="name">Name</option>
          <option value="printer">Printer</option>
          <option value="color">Color</option>
          <option value="class">Class</option>
        </select>
        <button
          type="button"
          aria-label="Toggle sort direction"
          className="inline-flex items-center gap-1 border rounded px-2 py-1 text-sm hover:bg-gray-50 bg-white"
          onClick={() => setSortDir(d => (d === 'asc' ? 'desc' : 'asc'))}
          title={sortDir === 'asc' ? 'Ascending' : 'Descending'}
        >
          {sortDir === 'asc' ? <ArrowUp className="w-4 h-4" /> : <ArrowDown className="w-4 h-4" />}
          <span className="sr-only">{sortDir === 'asc' ? 'Ascending' : 'Descending'}</span>
        </button>
        </div>
      </div>

      {isFetching && (
        <div className="mb-2 text-xs text-gray-500" aria-live="polite">Updating results…</div>
      )}
      {error && (
        <div className="mb-2 text-sm text-red-600" role="alert">{error}</div>
      )}

      {sortedJobs.length === 0 ? (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center">
          <p className="text-gray-500">No jobs found for this status.</p>
        </div>
      ) : (
        <div className={`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 transition-opacity duration-200 ${isFading ? 'opacity-0' : 'opacity-100'}`}>
        {sortedJobs.map(job => (
          <JobCard 
            key={job.id} 
            job={job} 
            currentStatus={filters?.status}
            onApprove={openApproveModal}
            onReject={handleReject}
            onMarkReviewed={handleMarkReviewed}
            onStatusAction={openStatusModal}
            onModalOpenChange={onModalOpenChange}
            expandSignal={expandAllSignal}
            collapseSignal={collapseAllSignal}
          />
        ))}
        </div>
      )}
      {approveJobId && (
        <ApprovalModal
          jobId={approveJobId}
          material={approveJobMaterial || undefined}
          currentPrinter={approveJobPrinter || undefined}
          onClose={closeApproveModal}
          onApproved={handleApprovedSuccess}
        />
      )}
      {statusJobId && statusAction === 'mark-picked-up' && (
        <PaymentModal
          jobId={statusJobId}
          onClose={closeStatusModal}
          onSuccess={handleStatusSuccess}
        />
      )}
      {statusJobId && statusAction && statusAction !== 'mark-picked-up' && (
        <StatusChangeModal
          jobId={statusJobId}
          action={statusAction}
          title={
            statusAction === 'mark-printing' ? 'Mark as Printing' :
            statusAction === 'mark-complete' ? 'Mark as Complete' :
            'Mark as Paid/Picked Up'
          }
          description={
            statusAction === 'mark-printing' ? 'This will move the job into Printing.' : 'This will move the job to Completed.'
          }
          confirmVerb={
            statusAction === 'mark-printing' ? 'Mark Printing' : 'Mark Complete'
          }
          onClose={closeStatusModal}
          onSuccess={handleStatusSuccess}
        />
      )}
    </div>
  );
}