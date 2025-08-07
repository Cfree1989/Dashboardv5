"use client";
import React, { useEffect, useMemo, useState } from "react";

type Staff = { name: string; is_active: boolean };

export interface RejectionModalProps {
  jobId: string;
  onClose: () => void;
  onRejected: () => void; // parent removes job from list
}

const DEFAULT_REASONS = [
  "Model walls too thin",
  "Unsupported overhangs",
  "File not manifold/has holes",
  "Exceeds printer size",
  "Inappropriate or non-compliant content",
];

export default function RejectionModal({ jobId, onClose, onRejected }: RejectionModalProps) {
  const [staff, setStaff] = useState<Staff[]>([]);
  const [loadingStaff, setLoadingStaff] = useState(false);
  const [staffName, setStaffName] = useState("");
  const [selectedReasons, setSelectedReasons] = useState<string[]>([]);
  const [customReason, setCustomReason] = useState<string>("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string>("");
  const [confirmOpen, setConfirmOpen] = useState(false);

  useEffect(() => {
    async function fetchStaff() {
      try {
        setLoadingStaff(true);
        setError("");
        const token = localStorage.getItem("token");
        const res = await fetch("/api/v1/staff", {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!res.ok) throw new Error("Failed to load staff");
        const data = await res.json();
        const list: Staff[] = (data?.staff || []).filter((s: Staff) => s.is_active);
        setStaff(list);
      } catch (e) {
        setError("Failed to load staff list");
      } finally {
        setLoadingStaff(false);
      }
    }
    fetchStaff();
  }, []);

  const hasReason = selectedReasons.length > 0 || customReason.trim().length > 0;
  const isValid = staffName.trim().length > 0 && hasReason;

  function toggleReason(reason: string) {
    setSelectedReasons((prev) =>
      prev.includes(reason) ? prev.filter((r) => r !== reason) : [...prev, reason]
    );
  }

  async function doReject() {
    try {
      setSubmitting(true);
      setError("");
      const token = localStorage.getItem("token");
      const res = await fetch(`/api/v1/jobs/${jobId}/reject`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          staff_name: staffName,
          reasons: selectedReasons,
          custom_reason: customReason.trim(),
        }),
      });
      if (!res.ok) {
        const text = await res.text();
        throw new Error(text || "Failed to reject job");
      }
      onRejected();
      onClose();
    } catch (err) {
      setError("Rejection failed. Please check inputs and try again.");
    } finally {
      setSubmitting(false);
      setConfirmOpen(false);
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!isValid) return;
    setConfirmOpen(true);
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <div className="relative bg-white w-full max-w-md rounded-xl shadow-lg border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Reject Job</h3>
        {error && (
          <div className="mb-3 text-sm text-red-600" role="alert">{error}</div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Performing Action As</label>
            <select
              className="w-full border rounded-lg px-3 py-2 focus-ring"
              value={staffName}
              onChange={(e) => setStaffName(e.target.value)}
              disabled={loadingStaff}
              required
            >
              <option value="" disabled>
                {loadingStaff ? "Loading staff..." : "Select your name"}
              </option>
              {staff.map((s) => (
                <option key={s.name} value={s.name}>
                  {s.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Reasons</label>
            <div className="space-y-2">
              {DEFAULT_REASONS.map((reason) => (
                <label key={reason} className="flex items-center space-x-2 text-sm text-gray-700">
                  <input
                    type="checkbox"
                    className="rounded border-gray-300"
                    checked={selectedReasons.includes(reason)}
                    onChange={() => toggleReason(reason)}
                  />
                  <span>{reason}</span>
                </label>
              ))}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Custom message (optional)</label>
                <textarea
                  className="w-full border rounded-lg px-3 py-2 focus-ring"
                  rows={3}
                  placeholder="Provide more details for the student..."
                  value={customReason}
                  onChange={(e) => setCustomReason(e.target.value)}
                />
              </div>
            </div>
          </div>

          <div className="flex justify-end space-x-2 pt-2">
            <button type="button" onClick={onClose} className="px-4 py-2 rounded-lg border text-gray-700 hover:bg-gray-50 focus-ring btn-transition">
              Cancel
            </button>
            <button
              type="submit"
              disabled={!isValid || submitting}
              className="px-4 py-2 rounded-lg bg-red-600 text-white hover:bg-red-700 disabled:opacity-50 focus-ring btn-transition"
            >
              {submitting ? "Rejecting..." : "Reject"}
            </button>
          </div>
          <p className="text-xs text-gray-500 mt-2">You will be asked to confirm on the next step.</p>
        </form>
      </div>
      {confirmOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="absolute inset-0 bg-black/40" onClick={() => setConfirmOpen(false)} />
          <div className="relative bg-white w-full max-w-sm rounded-xl shadow-lg border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-1">Are you sure?</h3>
            <p className="text-sm text-gray-600 mb-4">This will mark the job as Rejected.</p>
            <div className="flex justify-end space-x-2">
              <button onClick={() => setConfirmOpen(false)} className="px-4 py-2 rounded-lg border text-gray-700 hover:bg-gray-50 focus-ring btn-transition">Cancel</button>
              <button onClick={doReject} className="px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 focus-ring btn-transition">Yes, reject</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}


