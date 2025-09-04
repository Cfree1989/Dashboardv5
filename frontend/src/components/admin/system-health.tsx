"use client";
import React, { useEffect, useState } from "react";
import { AlertTriangle, CheckCircle, Clock, Trash2, ActivitySquare, Database, Mail } from "lucide-react";
import { useToast } from "../ui/toast";
import { apiClient } from "../../lib/unified-api-client";
import { createErrorState, updateErrorState, clearErrorState } from "../../lib/error-handling";
import { InlineError } from "../ui/error-display";

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
  const [error, setError] = useState(createErrorState());
  const { show } = useToast();
  const [diag, setDiag] = useState<any | null>(null);
  const [health, setHealth] = useState<any | null>(null);

  async function fetchReport() {
    try {
      setLoadingReport(true);
      setError(clearErrorState());
      
      // Add timestamp to prevent caching of audit reports
      const timestamp = Date.now();
      const data: ServerAuditReport = await apiClient.get(`/api/v1/admin/audit/report?t=${timestamp}`);
      setLastReport(data);
      setCurrentAudit(null);
      
      console.log(`🔄 Audit report refreshed at ${new Date().toLocaleTimeString()}:`, {
        orphaned_files: data.orphaned_files?.length || 0,
        broken_links: data.broken_links?.length || 0,
        stale_files: data.stale_files?.length || 0,
        files_scanned: (data as any).files_scanned || 0
      });
    } catch (e) {
      console.error('Failed to fetch audit report:', e);
      setError(updateErrorState(error, e));
    } finally {
      setLoadingReport(false);
    }
  }

  useEffect(() => {
    fetchReport();
    (async () => {
      try {
        const d = await apiClient.get('/api/v1/_diag');
        setDiag(d);
      } catch {}
      try {
        const h = await fetch('/api/v1/health');
        if (h.ok) setHealth(await h.json());
      } catch {}
    })();
  }, []);

  const startAudit = async () => {
    setIsStarting(true);
    setError(clearErrorState());
    setCurrentAudit({ startedAt: new Date().toISOString() });
    try {
      await fetchReport();
      show("Audit completed");
    } finally {
      setIsStarting(false);
    }
  };

  const cleanUpOrphans = async () => {
    if (!lastReport || !lastReport.orphaned_files?.length) {
      show("No orphaned files to clean up");
      return;
    }

    let successCount = 0;
    let failureCount = 0;
    const failures: string[] = [];

    show("Starting cleanup of orphaned files...");

    for (const path of lastReport.orphaned_files) {
      try {
        await apiClient.request("/api/v1/admin/audit/orphaned-file", {
          method: "DELETE",
          body: JSON.stringify({ file_path: path, staff_name: "Kiran Lutchman" })
        });
        successCount++;
        console.log(`✅ Successfully deleted orphaned file: ${path}`);
      } catch (error) {
        failureCount++;
        failures.push(`${path}: ${error}`);
        console.error(`❌ Failed to delete orphaned file ${path}:`, error);
      }
    }

    // Always refresh audit report after cleanup attempt
    await fetchReport();

    // Provide detailed user feedback
    if (failureCount === 0) {
      show(`✅ Successfully cleaned up ${successCount} orphaned file(s)`);
    } else if (successCount === 0) {
      show(`❌ Failed to clean up ${failureCount} orphaned file(s). Check console for details.`);
    } else {
      show(`⚠️ Partially successful: ${successCount} cleaned, ${failureCount} failed. Check console for details.`);
    }
  };

  const deleteStale = async (path: string) => {
    try {
      await apiClient.request("/api/v1/admin/audit/stale-file", {
        method: "DELETE",
        body: JSON.stringify({ file_path: path, staff_name: "Kiran Lutchman" })
      });
      // refresh
      await fetchReport();
    } catch (e) {
      setError(updateErrorState(error, e));
    }
  };

  const markReviewed = async (jobId: string, issues: string[]) => {
    try {
      await apiClient.post("/api/v1/admin/audit/mark-reviewed", { job_id: jobId, staff_name: "Kiran Lutchman", issues });
      show("Marked reviewed");
      // Refresh the report so the UI can reflect any state (if desired in future)
      await fetchReport();
    } catch (e) {
      setError(updateErrorState(error, e));
    }
  };

  const repairMetadata = async (jobId: string) => {
    try {
      await apiClient.post("/api/v1/admin/audit/repair-metadata", { job_id: jobId, staff_name: "Kiran Lutchman" });
      show("Metadata repaired");
      await fetchReport();
    } catch (e) {
      setError(updateErrorState(error, e));
    }
  };

  const repairLocation = async (jobId: string) => {
    try {
      await apiClient.post("/api/v1/admin/audit/repair-location", { job_id: jobId, staff_name: "Kiran Lutchman" });
      show("Location repaired");
      await fetchReport();
    } catch (e) {
      setError(updateErrorState(error, e));
    }
  };

  const relinkFile = async (jobId: string) => {
    const path = prompt('Enter full path to the authoritative file (under storage):');
    if (!path) return;
    try {
      await apiClient.post("/api/v1/admin/audit/relink-file", { job_id: jobId, staff_name: "Kiran Lutchman", file_path: path });
      show("File relinked");
      await fetchReport();
    } catch (e) {
      setError(updateErrorState(error, e));
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
          {/* Environment & Health summary */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div className="p-3 rounded-lg border">
              <div className="flex items-center text-sm text-gray-600"><ActivitySquare className="w-4 h-4 mr-2"/>Health</div>
              <div className={`text-lg font-semibold ${health?.status === 'ok' ? 'text-green-700' : 'text-red-700'}`}>{health?.status || 'unknown'}</div>
            </div>
            <div className="p-3 rounded-lg border">
              <div className="flex items-center text-sm text-gray-600"><Database className="w-4 h-4 mr-2"/>DB Engine</div>
              <div className="text-lg font-semibold">{diag?.db_engine || 'unknown'}</div>
              {diag?.migration_head && <div className="text-xs text-gray-500">alembic: {diag.migration_head}</div>}
            </div>
            <div className="p-3 rounded-lg border">
              <div className="flex items-center text-sm text-gray-600"><Mail className="w-4 h-4 mr-2"/>Email</div>
              <div className="text-lg font-semibold">{diag?.email_configured ? 'configured' : 'not set'}</div>
            </div>
          </div>
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-medium text-gray-900">Run System Audit</h3>
              <p className="text-sm text-gray-500">Scan for orphaned, broken, and stale files in the system</p>
            </div>
            <button
              onClick={startAudit}
              disabled={isStarting || !!currentAudit}
              className="px-4 py-2 bg-gray-800 text-white rounded-lg hover:bg-black disabled:opacity-50"
              title="Run a fresh integrity scan comparing storage to the database. Safe to click anytime."
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
            {error.hasError && (
              <div className="mb-3">
                <InlineError
                  error={error}
                  className="mb-2"
                />
              </div>
            )}
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
            {typeof (lastReport as any).files_scanned === 'number' && (
              <div className="text-sm text-gray-500 mb-2">Files scanned: {(lastReport as any).files_scanned}</div>
            )}

            {(lastReport.orphaned_files?.length || 0) > 0 ? (
              <div className="flex items-center justify-between p-3 bg-orange-50 rounded-lg">
                <div className="flex items-center space-x-2">
                  <AlertTriangle className="w-4 h-4 text-orange-600" />
                  <span className="text-sm text-orange-800">{lastReport.orphaned_files.length} orphaned files found</span>
                </div>
                <button
                  onClick={cleanUpOrphans}
                  className="px-3 py-1 text-xs rounded border border-gray-300 hover:bg-gray-50 flex items-center"
                  title="Delete files on disk that are not referenced by any job. Safe cleanup."
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
                      <button onClick={() => deleteStale(p)} className="text-yellow-800 hover:underline" title="Remove duplicate/stale copy. The job points to a different authoritative file.">Delete</button>
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
                        <div className="flex items-center gap-3">
                          <button
                            onClick={() => repairLocation(b.job_id)}
                            className="px-2 py-1 text-xs rounded-lg border border-purple-200 text-purple-700 bg-purple-50 hover:bg-purple-100 focus-ring btn-transition"
                            title="Move the job’s file and metadata into the folder that matches its current status. Use when you see dir_status_mismatch."
                          >
                            Repair Location
                          </button>
                          <button
                            onClick={() => repairMetadata(b.job_id)}
                            className="px-2 py-1 text-xs rounded-lg border border-blue-200 text-blue-700 bg-blue-50 hover:bg-blue-100 focus-ring btn-transition"
                            title="Create or fix metadata.json next to the authoritative file and sync status/file_path/display fields. Use for metadata_missing or metadata_mismatch."
                          >
                            Repair Metadata
                          </button>
                          <button
                            onClick={() => relinkFile(b.job_id)}
                            className="px-2 py-1 text-xs rounded-lg border border-gray-200 text-gray-800 bg-gray-50 hover:bg-gray-100 focus-ring btn-transition"
                            title="Point this job to a specific file under storage (then it will be moved to the correct status folder). Use when the authoritative file was moved or renamed."
                          >
                            Relink File
                          </button>
                          <button
                            onClick={() => markReviewed(b.job_id, b.issues || [])}
                            className="px-2 py-1 text-xs rounded-lg border border-red-200 text-red-700 bg-red-50 hover:bg-red-100 focus-ring btn-transition"
                            title="Log that you acknowledged this issue; does not remove it from the list."
                          >
                            Mark Reviewed
                          </button>
                        </div>
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


