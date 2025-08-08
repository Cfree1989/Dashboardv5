"use client";
import React, { useState } from "react";
import { Archive, Trash2, AlertTriangle } from "lucide-react";

export function DataManagementPanel() {
  const [archiveDays, setArchiveDays] = useState(90);
  const [pruneDays, setPruneDays] = useState(365);
  const [isArchiveOpen, setIsArchiveOpen] = useState(false);
  const [isPruneOpen, setIsPruneOpen] = useState(false);
  const [previewCounts, setPreviewCounts] = useState({ archive: 0, prune: 0 });
  const [isProcessing, setIsProcessing] = useState(false);

  const getArchivePreview = async () => {
    await new Promise((r) => setTimeout(r, 400));
    setPreviewCounts((p) => ({ ...p, archive: 45 }));
    setIsArchiveOpen(true);
  };
  const getPrunePreview = async () => {
    await new Promise((r) => setTimeout(r, 400));
    setPreviewCounts((p) => ({ ...p, prune: 12 }));
    setIsPruneOpen(true);
  };
  const executeArchive = async () => {
    setIsProcessing(true);
    try {
      await new Promise((r) => setTimeout(r, 800));
      setIsArchiveOpen(false);
    } finally {
      setIsProcessing(false);
    }
  };
  const executePrune = async () => {
    setIsProcessing(true);
    try {
      await new Promise((r) => setTimeout(r, 800));
      setIsPruneOpen(false);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="space-y-6">
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
            <label htmlFor="archive-days" className="text-sm text-gray-700">Archive jobs older than (days)</label>
            <input id="archive-days" type="number" min={1} value={archiveDays} onChange={(e) => setArchiveDays(Number(e.target.value))} className="mt-1 w-40 border border-gray-300 rounded px-3 py-2 text-sm" />
            <p className="text-sm text-gray-500 mt-1">Jobs in COMPLETED or PAIDPICKEDUP older than this will be archived.</p>
          </div>
          <button onClick={getArchivePreview} className="w-full px-4 py-2 bg-gray-800 text-white rounded-lg hover:bg-black">Preview Archive Operation</button>
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
            <input id="prune-days" type="number" min={1} value={pruneDays} onChange={(e) => setPruneDays(Number(e.target.value))} className="mt-1 w-40 border border-gray-300 rounded px-3 py-2 text-sm" />
            <p className="text-sm text-gray-500 mt-1">Archived jobs older than this will be permanently deleted.</p>
          </div>
          <button onClick={getPrunePreview} className="w-full px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700">Preview Prune Operation</button>
        </div>
      </div>

      {/* Archive Modal */}
      {isArchiveOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white rounded-xl shadow-xl border border-gray-200 w-full max-w-lg p-5">
            <h3 className="font-semibold mb-2">Confirm Archive Operation</h3>
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm text-blue-800 mb-3">
              <strong>{previewCounts.archive} jobs</strong> will be moved to archive storage.
            </div>
            <p className="text-sm text-gray-600 mb-4">Jobs older than {archiveDays} days in COMPLETED or PAIDPICKEDUP will be archived. This operation is reversible.</p>
            <div className="flex justify-end gap-2">
              <button onClick={() => setIsArchiveOpen(false)} className="px-3 py-2 text-sm rounded border border-gray-300">Cancel</button>
              <button onClick={executeArchive} disabled={isProcessing} className="px-3 py-2 text-sm rounded bg-gray-800 text-white disabled:opacity-50">{isProcessing ? "Archiving…" : "Archive Jobs"}</button>
            </div>
          </div>
        </div>
      )}

      {/* Prune Modal */}
      {isPruneOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white rounded-xl shadow-xl border border-gray-200 w-full max-w-lg p-5">
            <div className="flex items-center gap-2 text-red-600 mb-2"><AlertTriangle className="w-5 h-5" /><h3 className="font-semibold">Confirm Prune Operation</h3></div>
            <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-800 mb-3">
              <strong>Warning:</strong> {previewCounts.prune} archived jobs will be permanently deleted. This action cannot be undone.
            </div>
            <p className="text-sm text-gray-600 mb-4">Archived jobs older than {pruneDays} days will be permanently removed.</p>
            <div className="flex justify-end gap-2">
              <button onClick={() => setIsPruneOpen(false)} className="px-3 py-2 text-sm rounded border border-gray-300">Cancel</button>
              <button onClick={executePrune} disabled={isProcessing} className="px-3 py-2 text-sm rounded bg-red-600 text-white disabled:opacity-50">{isProcessing ? "Deleting…" : "Delete Jobs"}</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}


