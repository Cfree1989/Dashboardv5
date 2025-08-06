"use client";
import React, { useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import JobList from '../../components/dashboard/job-list';

const printerOptions = ['Prusa MK4S', 'Prusa XL', 'Raise3D Pro 2 Plus', 'Formlabs Form 3'];
const disciplineOptions = ['Art', 'Architecture', 'Landscape Architecture', 'Interior Design', 'Engineering', 'Hobby/Personal', 'Other'];
const statusOptions = ['UPLOADED', 'PENDING', 'READYTOPRINT', 'PRINTING', 'COMPLETED', 'PAIDPICKEDUP', 'ARCHIVED'];

export default function DashboardPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialSearch = searchParams.get('search') || '';
  const initialPrinter = searchParams.get('printer') || '';
  const initialDiscipline = searchParams.get('discipline') || '';
  const initialStatus = searchParams.get('status') || statusOptions[0];
  const [search, setSearch] = useState(initialSearch);
  const [printer, setPrinter] = useState(initialPrinter);
  const [discipline, setDiscipline] = useState(initialDiscipline);
  const [status, setStatus] = useState(initialStatus);
  const updateFilters = (filters: {search?: string; printer?: string; discipline?: string; status?: string}) => {
    const params = new URLSearchParams();
    if (filters.search) params.set('search', filters.search);
    if (filters.printer) params.set('printer', filters.printer);
    if (filters.discipline) params.set('discipline', filters.discipline);
    if (filters.status) params.set('status', filters.status);
    const query = params.toString();
    router.replace(`${window.location.pathname}${query ? `?${query}` : ''}`);
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Staff Dashboard</h1>
      <div className="mb-4 flex space-x-4">
        <input
          type="text"
          placeholder="Search by student name or ID"
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="border rounded p-2 flex-1"
        />
        <select
          value={printer}
          onChange={e => setPrinter(e.target.value)}
          className="border rounded p-2"
        >
          <option value="">All Printers</option>
          {printerOptions.map(opt => <option key={opt} value={opt}>{opt}</option>)}
        </select>
        <select
          value={discipline}
          onChange={e => setDiscipline(e.target.value)}
          className="border rounded p-2"
        >
          <option value="">All Disciplines</option>
          {disciplineOptions.map(opt => <option key={opt} value={opt}>{opt}</option>)}
        </select>
      </div>
      <div className="mb-4 flex space-x-2">
        {statusOptions.map(s => (
          <button
            key={s}
            onClick={() => setStatus(s)}
            className={`px-3 py-1 rounded ${status===s? 'bg-blue-600 text-white':'bg-gray-200'}`}
          >
            {s}
          </button>
        ))}
      </div>
      <JobList filters={{ status, search, printer, discipline }} />
    </div>
  );
}