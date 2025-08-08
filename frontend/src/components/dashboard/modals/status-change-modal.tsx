"use client";
import React, { useEffect, useState } from "react";

type Staff = { name: string; is_active: boolean };

export interface StatusChangeModalProps {
  jobId: string;
  action: "mark-printing" | "mark-complete" | "mark-picked-up";
  title: string;
  description: string;
  confirmVerb: string; // e.g., "Mark Printing"
  onClose: () => void;
  onSuccess: () => void; // parent removes job from list & refreshes counts
}

export default function StatusChangeModal({ jobId, action, title, description, confirmVerb, onClose, onSuccess }: StatusChangeModalProps) {
  const [staff, setStaff] = useState<Staff[]>([]);
  const [loadingStaff, setLoadingStaff] = useState(false);
  const [staffName, setStaffName] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string>("");
  const [confirmOpen, setConfirmOpen] = useState(false);

  useEffect(() => {
    async function fetchStaff() {
      try {
        setLoadingStaff(true);
        setError("");
        const token = localStorage.getItem("token");
        const res = await fetch("/api/v1/staff", { headers: { Authorization: `Bearer ${token}` } });
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

  const isValid = staffName.trim().length > 0;

  async function doSubmit() {
    try {
      setSubmitting(true);
      setError("");
      const token = localStorage.getItem("token");
      const res = await fetch(`/api/v1/jobs/${jobId}/${action}`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ staff_name: staffName }),
      });
      if (!res.ok) {
        const txt = await res.text();
        throw new Error(txt || "Request failed");
      }
      onSuccess();
      onClose();
    } catch (e) {
      setError("Action failed. Please try again.");
    } finally {
      setSubmitting(false);
      setConfirmOpen(false);
    }
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!isValid) return;
    setConfirmOpen(true);
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <div className="relative bg-white w-full max-w-md rounded-xl shadow-lg border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-1">{title}</h3>
        <p className="text-sm text-gray-600 mb-4">{description}</p>
        {error && <div className="mb-3 text-sm text-red-600" role="alert">{error}</div>}

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
                <option key={s.name} value={s.name}>{s.name}</option>
              ))}
            </select>
          </div>

          <div className="flex justify-end space-x-2 pt-2">
            <button type="button" onClick={onClose} className="px-4 py-2 rounded-lg border text-gray-700 hover:bg-gray-50 focus-ring btn-transition">Cancel</button>
            <button type="submit" disabled={!isValid || submitting} className="px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 focus-ring btn-transition">
              {submitting ? `${confirmVerb}...` : confirmVerb}
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
            <p className="text-sm text-gray-600 mb-4">This will immediately apply the change.</p>
            <div className="flex justify-end space-x-2">
              <button onClick={() => setConfirmOpen(false)} className="px-4 py-2 rounded-lg border text-gray-700 hover:bg-gray-50 focus-ring btn-transition">Cancel</button>
              <button onClick={doSubmit} className="px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 focus-ring btn-transition">{confirmVerb}</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}


