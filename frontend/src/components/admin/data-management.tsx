"use client";
import React, { useState } from "react";
import { Archive, Trash2, AlertTriangle, CheckCircle, Settings } from "lucide-react";
import { useToast } from "../ui/toast";
import { CatalogEditor } from "./catalog-editor";
import { apiRequest } from "../../lib/auth";

export function DataManagementPanel() {
  const [archiveDays, setArchiveDays] = useState(45);
  const [pruneDays, setPruneDays] = useState(365);
  const [isArchiveOpen, setIsArchiveOpen] = useState(false);
  const [isPruneOpen, setIsPruneOpen] = useState(false);
  const [previewCounts, setPreviewCounts] = useState<{ archive?: number | null; prune?: number | null }>({});
  const [isProcessing, setIsProcessing] = useState(false);
  const [staffName, setStaffName] = useState("");
  const [errorMsg, setErrorMsg] = useState("");
  const [successMsg, setSuccessMsg] = useState("");
  const { show } = useToast();

  const openArchiveConfirm = () => {
    setErrorMsg("");
    setSuccessMsg("");
    setPreviewCounts((p) => ({ ...p, archive: null }));
    setIsArchiveOpen(true);
  };
  const openPruneConfirm = () => {
    setErrorMsg("");
    setSuccessMsg("");
    setPreviewCounts((p) => ({ ...p, prune: null }));
    setIsPruneOpen(true);
  };
  const executeArchive = async () => {
    setIsProcessing(true);
    setErrorMsg("");
    setSuccessMsg("");
    try {
      const data = await apiRequest(`/api/v1/admin/archive`, {
        method: "POST",
        body: JSON.stringify({ retention_days: archiveDays, staff_name: staffName.trim() }),
      });
      const count = Number(data?.jobs_archived ?? 0);
      setPreviewCounts((p) => ({ ...p, archive: isNaN(count) ? 0 : count }));
      setSuccessMsg(`Archived ${count} job(s).`);
      show(`Archive completed: ${count} job(s)`);
    } catch {
      setErrorMsg("Network error while archiving.");
    } finally {
      setIsProcessing(false);
    }
  };
  const executePrune = async () => {
    setIsProcessing(true);
    setErrorMsg("");
    setSuccessMsg("");
    try {
      const data = await apiRequest(`/api/v1/admin/prune`, {
        method: "POST",
        body: JSON.stringify({ retention_days: pruneDays, staff_name: staffName.trim() }),
      });
      const count = Number(data?.jobs_deleted ?? 0);
      setPreviewCounts((p) => ({ ...p, prune: isNaN(count) ? 0 : count }));
      setSuccessMsg(`Deleted ${count} archived job(s).`);
      show(`Prune completed: ${count} job(s)`);
    } catch {
      setErrorMsg("Network error while pruning.");
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Catalog Editor */}
      <CatalogEditor featureFlag={true} />
      
      {/* Archive Jobs */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        <div className="px-5 py-4 border-b border-gray-100">
          <h2 className="text-base font-semibold text-gray-900 flex items-center gap-2">
            <Archive className="w-5 h-5 text-blue-500" />
            Archive Jobs
          </h2>
          <p className="text-sm text-gray-600">Move completed jobs to archive storage to free up active space.</p>
        </div>
        <div className="p-5 space-y-3">
          <div>
            <label htmlFor="staff-name" className="text-sm text-gray-700">Performing Action As (Staff Name)</label>
            <input id="staff-name" type="text" value={staffName} onChange={(e) => setStaffName(e.target.value)} placeholder="Enter your staff name"
              className="mt-1 w-full border border-gray-300 rounded px-3 py-2 text-sm" />
            <p className="text-xs text-gray-500 mt-1">All admin actions are audited with this name.</p>
          </div>
          <div>
            <label htmlFor="archive-days" className="text-sm text-gray-700">Archive jobs older than (days)</label>
            <input id="archive-days" type="number" min={0} value={archiveDays} onChange={(e) => setArchiveDays(Number(e.target.value))} className="mt-1 w-40 border border-gray-300 rounded px-3 py-2 text-sm" />
            <p className="text-sm text-gray-500 mt-1">Jobs in COMPLETED or PAIDPICKEDUP older than this will be archived.</p>
          </div>
          <button onClick={openArchiveConfirm} disabled={!staffName.trim()} className="w-full px-4 py-2 bg-gray-800 text-white rounded-lg hover:bg-black disabled:opacity-50">Review & Archive</button>
        </div>
      </div>

      {/* Prune Archived Jobs */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        <div className="px-5 py-4 border-b border-gray-100">
          <h2 className="text-base font-semibold text-gray-900 flex items-center gap-2">
            <Trash2 className="w-5 h-5 text-red-500" />
            Prune Archived Jobs
          </h2>
          <p className="text-sm text-gray-600">Permanently delete old archived jobs to free storage.</p>
        </div>
        <div className="p-5 space-y-3">
          <div>
            <label htmlFor="prune-days" className="text-sm text-gray-700">Delete archived jobs older than (days)</label>
            <input id="prune-days" type="number" min={0} value={pruneDays} onChange={(e) => setPruneDays(Number(e.target.value))} className="mt-1 w-40 border border-gray-300 rounded px-3 py-2 text-sm" />
            <p className="text-sm text-gray-500 mt-1">Archived jobs older than this will be permanently deleted.</p>
          </div>
          <button onClick={openPruneConfirm} disabled={!staffName.trim()} className="w-full px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50">Review & Prune</button>
        </div>
      </div>

      {/* Archive Modal */}
      {isArchiveOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white rounded-xl shadow-xl border border-gray-200 w-full max-w-lg p-5">
            <h3 className="font-semibold mb-2">Confirm Archive Operation</h3>
            {errorMsg && (<div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-800 mb-3" role="alert">{errorMsg}</div>)}
            {successMsg && (<div className="bg-green-50 border border-green-200 rounded-lg p-3 text-sm text-green-800 mb-3" role="status">{successMsg}</div>)}
            <p className="text-sm text-gray-600 mb-2">Jobs older than <strong>{archiveDays}</strong> days in COMPLETED or PAIDPICKEDUP will be archived.</p>
            {typeof previewCounts.archive === 'number' && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm text-blue-800 mb-3">Archived {previewCounts.archive} job(s).</div>
            )}
            <div className="flex justify-end gap-2">
              <button onClick={() => setIsArchiveOpen(false)} className="px-3 py-2 text-sm rounded border border-gray-300">{successMsg ? "Close" : "Cancel"}</button>
              {!successMsg && (
                <button onClick={executeArchive} disabled={isProcessing} className="px-3 py-2 text-sm rounded bg-gray-800 text-white disabled:opacity-50 flex items-center gap-1">
                  {isProcessing ? (<><span className="inline-block h-3 w-3 rounded-full border border-white border-t-transparent animate-spin" /> Archiving…</>) : (<>Archive Jobs <CheckCircle className="w-4 h-4" /></>)}
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Prune Modal */}
      {isPruneOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white rounded-xl shadow-xl border border-gray-200 w-full max-w-lg p-5">
            <div className="flex items-center gap-2 text-red-600 mb-2"><AlertTriangle className="w-5 h-5" /><h3 className="font-semibold">Confirm Prune Operation</h3></div>
            {errorMsg && (<div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-800 mb-3" role="alert">{errorMsg}</div>)}
            {successMsg && (<div className="bg-green-50 border border-green-200 rounded-lg p-3 text-sm text-green-800 mb-3" role="status">{successMsg}</div>)}
            <p className="text-sm text-gray-600 mb-2">Archived jobs older than <strong>{pruneDays}</strong> days will be permanently removed.</p>
            {typeof previewCounts.prune === 'number' && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-800 mb-3">Deleted {previewCounts.prune} archived job(s).</div>
            )}
            <div className="flex justify-end gap-2">
              <button onClick={() => setIsPruneOpen(false)} className="px-3 py-2 text-sm rounded border border-gray-300">{successMsg ? "Close" : "Cancel"}</button>
              {!successMsg && (
                <button onClick={executePrune} disabled={isProcessing} className="px-3 py-2 text-sm rounded bg-red-600 text-white disabled:opacity-50">{isProcessing ? "Deleting…" : "Delete Jobs"}</button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}


