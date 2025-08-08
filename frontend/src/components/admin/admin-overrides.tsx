"use client";
import React, { useState } from "react";
import { AlertTriangle, Unlock, CheckCircle, RotateCcw, XCircle } from "lucide-react";

export function AdminOverridesPanel() {
  const [jobId, setJobId] = useState("");
  const [selectedAction, setSelectedAction] = useState("");
  const [reason, setReason] = useState("");
  const [newStatus, setNewStatus] = useState("");
  const [isConfirmOpen, setIsConfirmOpen] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);

  const actions = [
    { value: "unlock", label: "Force Unlock", icon: Unlock, description: "Remove any locks on the job" },
    { value: "confirm", label: "Force Confirm", icon: CheckCircle, description: "Mark job as confirmed without normal checks" },
    { value: "change_status", label: "Change Status", icon: RotateCcw, description: "Manually change job status" },
    { value: "mark_failed", label: "Mark Failed", icon: XCircle, description: "Mark job as failed with reason" },
  ];

  const statusOptions = ["UPLOADED", "PENDING", "READYTOPRINT", "PRINTING", "COMPLETED", "PAIDPICKEDUP", "REJECTED"];

  const onSubmit = () => {
    if (!jobId.trim() || !selectedAction || !reason.trim()) return;
    if (selectedAction === "change_status" && !newStatus) return;
    setIsConfirmOpen(true);
  };

  const executeOverride = async () => {
    setIsProcessing(true);
    try {
      // TODO: call admin override endpoints when available
      await new Promise((r) => setTimeout(r, 1000));
      setJobId("");
      setSelectedAction("");
      setReason("");
      setNewStatus("");
      setIsConfirmOpen(false);
    } finally {
      setIsProcessing(false);
    }
  };

  const SelectedIcon = actions.find((a) => a.value === selectedAction)?.icon ?? AlertTriangle;

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        <div className="px-5 py-4 border-b border-gray-100">
          <h2 className="text-base font-semibold text-gray-900 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-orange-500" />
            Admin Overrides
          </h2>
          <p className="text-sm text-gray-600 mt-1">Use these tools carefully. All actions are logged and require confirmation.</p>
        </div>
        <div className="p-5 space-y-4">
          <div>
            <label htmlFor="job-id" className="text-sm text-gray-700">Job ID</label>
            <input id="job-id" value={jobId} onChange={(e) => setJobId(e.target.value)} placeholder="Enter the job ID to modify" className="mt-1 w-full border border-gray-300 rounded px-3 py-2 text-sm" />
          </div>

          <div>
            <label htmlFor="action" className="text-sm text-gray-700">Action</label>
            <div className="mt-1">
              <select value={selectedAction} onChange={(e) => setSelectedAction(e.target.value)} className="w-full border border-gray-300 rounded px-3 py-2 text-sm">
                <option value="">Select an action</option>
                {actions.map((a) => (
                  <option key={a.value} value={a.value}>{a.label}</option>
                ))}
              </select>
            </div>
            {selectedAction && (
              <p className="text-sm text-gray-500 mt-1">{actions.find((a) => a.value === selectedAction)?.description}</p>
            )}
          </div>

          {selectedAction === "change_status" && (
            <div>
              <label htmlFor="new-status" className="text-sm text-gray-700">New Status</label>
              <div className="mt-1">
                <select value={newStatus} onChange={(e) => setNewStatus(e.target.value)} className="w-full border border-gray-300 rounded px-3 py-2 text-sm">
                  <option value="">Select new status</option>
                  {statusOptions.map((s) => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
              </div>
            </div>
          )}

          <div>
            <label htmlFor="reason" className="text-sm text-gray-700">Reason (Required)</label>
            <textarea id="reason" value={reason} onChange={(e) => setReason(e.target.value)} rows={3} placeholder="Explain why this override is necessary..." className="mt-1 w-full border border-gray-300 rounded px-3 py-2 text-sm" />
          </div>

          <button onClick={onSubmit} disabled={!jobId.trim() || !selectedAction || !reason.trim() || (selectedAction === "change_status" && !newStatus)} className="w-full px-4 py-2 bg-gray-800 text-white rounded-lg hover:bg-black disabled:opacity-50">Execute Override</button>
        </div>
      </div>

      {isConfirmOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white rounded-xl shadow-xl border border-gray-200 w-full max-w-lg p-5">
            <div className="flex items-center gap-2 text-red-600 mb-3">
              <SelectedIcon className="w-5 h-5" />
              <h3 className="font-semibold">Confirm Admin Override</h3>
            </div>
            <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-800 mb-3">
              <strong>Warning:</strong> This action will be logged and attributed. Proceed only if necessary.
            </div>
            <div className="text-sm space-y-1 mb-4">
              <div><strong>Job ID:</strong> {jobId}</div>
              <div><strong>Action:</strong> {actions.find((a) => a.value === selectedAction)?.label}</div>
              {selectedAction === "change_status" && (<div><strong>New Status:</strong> {newStatus}</div>)}
              <div><strong>Reason:</strong> {reason}</div>
            </div>
            <div className="flex justify-end gap-2">
              <button onClick={() => setIsConfirmOpen(false)} className="px-3 py-2 text-sm rounded border border-gray-300">Cancel</button>
              <button onClick={executeOverride} disabled={isProcessing} className="px-3 py-2 text-sm rounded bg-red-600 text-white disabled:opacity-50">{isProcessing ? "Processing…" : "Confirm Override"}</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}


