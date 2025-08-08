"use client";
import React, { useEffect, useState } from "react";
import { AlertTriangle, CheckCircle, Clock, Trash2 } from "lucide-react";

type ServerAuditReport = {
  report_generated_at: string;
  orphaned_files: string[];
  broken_links: { job_id: string; issues: string[]; file_path?: string; metadata_path?: string; expected_dir?: string; actual_dir?: string }[];
  stale_files: string[];
};

export function SystemHealthPanel() {
  const [currentAudit, setCurrentAudit] = useState<{ startedAt: string } | null>(null);
  const [lastReport, setLastReport] = useState<ServerAuditReport | null>(null);
  const [isStarting, setIsStarting] = useState(false);
  const [loadingReport, setLoadingReport] = useState(false);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
    async function fetchReport() {
      try {
        setLoadingReport(true);
        setError("");
        const res = await fetch("/api/v1/admin/audit/report", { headers: { Authorization: `Bearer ${token}` } });
        if (!res.ok) throw new Error("Failed to load audit report");
        const data: ServerAuditReport = await res.json();
        setLastReport(data);
      } catch (e) {
        setError("Failed to load audit report");
      } finally {
        setLoadingReport(false);
      }
    }
    fetchReport();
  }, []);

  const startAudit = async () => {
    setIsStarting(true);
    try {
      // For now, synchronous scan via report fetch
      setCurrentAudit({ startedAt: new Date().toISOString() });
      const token = localStorage.getItem("token");
      const res = await fetch("/api/v1/admin/audit/report", { headers: { Authorization: `Bearer ${token}` } });
      if (res.ok) {
        const data: ServerAuditReport = await res.json();
        setLastReport(data);
      }
    } finally {
      setIsStarting(false);
    }
  };

  const cleanUpOrphans = async () => {
    if (!lastReport) return;
    const token = localStorage.getItem("token");
    for (const path of lastReport.orphaned_files) {
      await fetch("/api/v1/admin/audit/orphaned-file", {
        method: "DELETE",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ file_path: path, staff_name: "Admin User" }),
      });
    }
    // refresh
    const res = await fetch("/api/v1/admin/audit/report", { headers: { Authorization: `Bearer ${token}` } });
    if (res.ok) setLastReport(await res.json());
  };

  const deleteStale = async (path: string) => {
    try {
      const token = localStorage.getItem("token");
      await fetch("/api/v1/admin/audit/stale-file", {
        method: "DELETE",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ file_path: path, staff_name: "Admin User" }),
      });
      // refresh
      const res = await fetch("/api/v1/admin/audit/report", { headers: { Authorization: `Bearer ${token}` } });
      if (res.ok) setLastReport(await res.json());
    } catch {
      setError("Failed to delete stale file");
    }
  };

  const markReviewed = async (jobId: string, issues: string[]) => {
    try {
      const token = localStorage.getItem("token");
      await fetch("/api/v1/admin/audit/mark-reviewed", {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ job_id: jobId, staff_name: "Admin User", issues }),
      });
    } catch {
      setError("Failed to mark as reviewed");
    }
  };

  return (
    <div className="space-y-6">
      {/* System Integrity Audit card */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        <div className="px-5 py-4 border-b border-gray-100">
          <h2 className="text-base font-semibold text-gray-900">System Integrity Audit</h2>
        </div>
        <div className="p-5">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-medium text-gray-900">Run System Audit</h3>
              <p className="text-sm text-gray-500">Scan for orphaned, broken, and stale files in the system</p>
            </div>
            <button
              onClick={startAudit}
              disabled={isStarting || !!currentAudit}
              className="px-4 py-2 bg-gray-800 text-white rounded-lg hover:bg-black disabled:opacity-50"
            >
              {isStarting ? "Starting…" : "Start Audit"}
            </button>
          </div>

          {currentAudit && (
            <div className="mt-4 flex items-center space-x-2 p-3 bg-blue-50 rounded-lg">
              <Clock className="w-4 h-4 text-blue-600" />
              <span className="text-sm text-blue-800">
                Audit in progress… Started at {new Date(currentAudit.startedAt).toLocaleTimeString()}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Last Audit Report card */}
      {lastReport && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200">
            <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
            <h2 className="text-base font-semibold text-gray-900">Last Audit Report</h2>
              <span className="text-xs px-2 py-1 rounded-full bg-gray-900 text-white">completed</span>
          </div>
          <div className="p-5">
            {error && <div className="mb-3 text-sm text-red-600" role="alert">{error}</div>}
            {loadingReport && <div className="mb-3 text-sm text-gray-500">Loading report…</div>}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-900">{(lastReport.broken_links?.length || 0) + (lastReport.orphaned_files?.length || 0) + (lastReport.stale_files?.length || 0)}</div>
                <div className="text-sm text-gray-500">Files Scanned</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-orange-600">{lastReport.orphaned_files?.length || 0}</div>
                <div className="text-sm text-gray-500">Orphaned Files</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-red-600">{lastReport.broken_links?.length || 0}</div>
                <div className="text-sm text-gray-500">Broken Files</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-yellow-600">{lastReport.stale_files?.length || 0}</div>
                <div className="text-sm text-gray-500">Stale Files</div>
              </div>
            </div>

            <div className="text-sm text-gray-500 mb-4">Generated: {new Date(lastReport.report_generated_at).toLocaleString()}</div>

            {(lastReport.orphaned_files?.length || 0) > 0 ? (
              <div className="flex items-center justify-between p-3 bg-orange-50 rounded-lg">
                <div className="flex items-center space-x-2">
                  <AlertTriangle className="w-4 h-4 text-orange-600" />
                  <span className="text-sm text-orange-800">{lastReport.orphaned_files.length} orphaned files found</span>
                </div>
                <button
                  onClick={cleanUpOrphans}
                  className="px-3 py-1 text-xs rounded border border-gray-300 hover:bg-gray-50 flex items-center"
                >
                  <Trash2 className="w-4 h-4 mr-1" />
                  Clean Up
                </button>
              </div>
            ) : (
              <div className="flex items-center space-x-2 p-3 bg-green-50 rounded-lg">
                <CheckCircle className="w-4 h-4 text-green-600" />
                <span className="text-sm text-green-800">System integrity check passed — no issues found</span>
              </div>
            )}

            {/* Stale Files List */}
            {(lastReport.stale_files?.length || 0) > 0 && (
              <div className="mt-4">
                <h3 className="text-sm font-medium text-gray-900 mb-2">Stale Files</h3>
                <ul className="space-y-2 max-h-56 overflow-auto">
                  {lastReport.stale_files.map((p) => (
                    <li key={p} className="flex items-center justify-between text-xs bg-yellow-50 border border-yellow-100 rounded px-2 py-1">
                      <span className="truncate mr-2" title={p}>{p}</span>
                      <button onClick={() => deleteStale(p)} className="text-yellow-800 hover:underline">Delete</button>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Broken Links List */}
            {(lastReport.broken_links?.length || 0) > 0 && (
              <div className="mt-4">
                <h3 className="text-sm font-medium text-gray-900 mb-2">Broken Links</h3>
                <ul className="space-y-2 max-h-56 overflow-auto">
                  {lastReport.broken_links.map((b, idx) => (
                    <li key={`${b.job_id}-${idx}`} className="text-xs bg-red-50 border border-red-100 rounded px-2 py-2">
                      <div className="flex items-center justify-between">
                        <div className="font-medium text-red-800">Job {b.job_id}</div>
                        <button onClick={() => markReviewed(b.job_id, b.issues || [])} className="text-red-800 hover:underline">Mark Reviewed</button>
                      </div>
                      <div className="text-red-700 mt-1">Issues: {b.issues?.join(', ') || 'unknown'}</div>
                      {b.file_path && <div className="text-gray-500">File: {b.file_path}</div>}
                      {b.metadata_path && <div className="text-gray-500">Meta: {b.metadata_path}</div>}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}


