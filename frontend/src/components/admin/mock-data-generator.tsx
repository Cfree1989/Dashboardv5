"use client";

import { useState } from "react";
import { Trash2, Database, AlertTriangle, CheckCircle, Loader2 } from "lucide-react";

interface MockJobCounts {
  UPLOADED: number;
  PENDING: number;
  READYTOPRINT: number;
  PRINTING: number;
  COMPLETED: number;
  PAIDPICKEDUP: number;
}

interface DeleteAllResponse {
  message: string;
  deleted_counts: {
    jobs_deleted: number;
    events_deleted: number;
    payments_deleted: number;
  };
  total_before: {
    jobs: number;
    events: number;
    payments: number;
  };
}

export function MockDataGenerator() {
  const [isLoading, setIsLoading] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [counts, setCounts] = useState<MockJobCounts>({
    UPLOADED: 0,
    PENDING: 0,
    READYTOPRINT: 0,
    PRINTING: 0,
    COMPLETED: 0,
    PAIDPICKEDUP: 0,
  });
  const [email, setEmail] = useState("cfree3@lsu.edu");
  const [addNotes, setAddNotes] = useState(true);
  const [seed, setSeed] = useState("");
  const [confirmDelete, setConfirmDelete] = useState(false);

  const handleCountChange = (status: keyof MockJobCounts, value: string) => {
    const numValue = parseInt(value) || 0;
    setCounts(prev => ({ ...prev, [status]: numValue }));
  };

  const generateMockJobs = async () => {
    const totalRequested = Object.values(counts).reduce((sum, count) => sum + count, 0);
    if (totalRequested === 0) {
      setMessage({ type: 'error', text: 'Please specify at least one job to create.' });
      return;
    }

    setIsLoading(true);
    setMessage(null);

    try {
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('No authentication token found');
      }

      const response = await fetch('/api/v1/admin/mock-jobs', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          counts,
          email,
          addNotes,
          seed: seed ? parseInt(seed) : undefined,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || 'Failed to generate mock jobs');
      }

      const createdCounts = data.created_counts;
      const totalCreated = Object.values(createdCounts).reduce((sum: number, count: number) => sum + count, 0);
      
      setMessage({
        type: 'success',
        text: `Successfully generated ${totalCreated} mock jobs! Created: ${Object.entries(createdCounts)
          .filter(([_, count]) => (count as number) > 0)
          .map(([status, count]) => `${status}: ${count}`)
          .join(', ')}`
      });

      // Clear form after successful generation
      setCounts({
        UPLOADED: 0,
        PENDING: 0,
        READYTOPRINT: 0,
        PRINTING: 0,
        COMPLETED: 0,
        PAIDPICKEDUP: 0,
      });
      setSeed("");

    } catch (error) {
      setMessage({
        type: 'error',
        text: error instanceof Error ? error.message : 'An unexpected error occurred'
      });
    } finally {
      setIsLoading(false);
    }
  };

  const deleteAllJobs = async () => {
    if (!confirmDelete) {
      setMessage({ type: 'error', text: 'Please check the confirmation box to delete all jobs.' });
      return;
    }

    setIsDeleting(true);
    setMessage(null);

    try {
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('No authentication token found');
      }

      const response = await fetch('/api/v1/admin/delete-all-jobs', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ confirm: true }),
      });

      const data: DeleteAllResponse = await response.json();

      if (!response.ok) {
        throw new Error(data.message || 'Failed to delete all jobs');
      }

      setMessage({
        type: 'success',
        text: `Successfully deleted all jobs! Deleted: ${data.deleted_counts.jobs_deleted} jobs, ${data.deleted_counts.events_deleted} events, ${data.deleted_counts.payments_deleted} payments`
      });

      setConfirmDelete(false);

    } catch (error) {
      setMessage({
        type: 'error',
        text: error instanceof Error ? error.message : 'An unexpected error occurred'
      });
    } finally {
      setIsDeleting(false);
    }
  };

  const totalRequested = Object.values(counts).reduce((sum, count) => sum + count, 0);

  return (
    <div className="space-y-6">
      {/* Mock Data Generator Card */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex items-center gap-2 mb-4">
          <Database className="h-5 w-5 text-blue-600" />
          <h2 className="text-xl font-semibold">Mock Data Generator</h2>
        </div>
        <p className="text-gray-600 mb-6">
          Generate realistic mock jobs for testing. Only available in development mode.
        </p>

        {/* Job Counts */}
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-6">
          {Object.entries(counts).map(([status, count]) => (
            <div key={status} className="space-y-2">
              <label htmlFor={status} className="block text-sm font-medium text-gray-700">
                {status}
              </label>
              <input
                id={status}
                type="number"
                min="0"
                max="50"
                value={count}
                onChange={(e) => handleCountChange(status as keyof MockJobCounts, e.target.value)}
                placeholder="0"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          ))}
        </div>

        {/* Options */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="space-y-2">
            <label htmlFor="email" className="block text-sm font-medium text-gray-700">
              Email Address
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="cfree3@lsu.edu"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div className="space-y-2">
            <label htmlFor="seed" className="block text-sm font-medium text-gray-700">
              Random Seed (optional)
            </label>
            <input
              id="seed"
              type="number"
              value={seed}
              onChange={(e) => setSeed(e.target.value)}
              placeholder="Leave empty for random"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div className="flex items-center space-x-2">
            <input
              id="add-notes"
              type="checkbox"
              checked={addNotes}
              onChange={(e) => setAddNotes(e.target.checked)}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label htmlFor="add-notes" className="text-sm font-medium text-gray-700">
              Add Notes
            </label>
          </div>
        </div>

        {/* Generate Button */}
        <button
          onClick={generateMockJobs}
          disabled={isLoading || totalRequested === 0}
          className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {isLoading ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Generating...
            </>
          ) : (
            <>
              <Database className="h-4 w-4" />
              Generate {totalRequested} Mock Jobs
            </>
          )}
        </button>

        {totalRequested > 0 && (
          <p className="text-sm text-gray-500 text-center mt-2">
            Will generate {totalRequested} jobs with email: {email}
          </p>
        )}
      </div>

      {/* Delete All Jobs Card */}
      <div className="bg-white rounded-xl shadow-sm border border-red-200 p-6">
        <div className="flex items-center gap-2 mb-4">
          <Trash2 className="h-5 w-5 text-red-600" />
          <h2 className="text-xl font-semibold text-red-600">Delete All Jobs</h2>
        </div>
        <p className="text-red-600 mb-6">
          ⚠️ This will permanently delete ALL jobs from the entire system. This action cannot be undone.
        </p>

        <div className="flex items-center space-x-2 mb-4">
          <input
            id="confirm-delete"
            type="checkbox"
            checked={confirmDelete}
            onChange={(e) => setConfirmDelete(e.target.checked)}
            className="h-4 w-4 text-red-600 focus:ring-red-500 border-gray-300 rounded"
          />
          <label htmlFor="confirm-delete" className="text-sm font-medium text-red-600">
            I understand this will delete ALL jobs and cannot be undone
          </label>
        </div>

        <button
          onClick={deleteAllJobs}
          disabled={isDeleting || !confirmDelete}
          className="w-full bg-red-600 text-white py-2 px-4 rounded-md hover:bg-red-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {isDeleting ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Deleting All Jobs...
            </>
          ) : (
            <>
              <Trash2 className="h-4 w-4" />
              Delete All Jobs
            </>
          )}
        </button>
      </div>

      {/* Messages */}
      {message && (
        <div className={`p-4 rounded-md border ${
          message.type === 'success' 
            ? 'bg-green-50 border-green-200 text-green-800' 
            : 'bg-red-50 border-red-200 text-red-800'
        }`}>
          <div className="flex items-center gap-2">
            {message.type === 'success' ? (
              <CheckCircle className="h-4 w-4 text-green-600" />
            ) : (
              <AlertTriangle className="h-4 w-4 text-red-600" />
            )}
            <span className="text-sm font-medium">{message.text}</span>
          </div>
        </div>
      )}
    </div>
  );
}
