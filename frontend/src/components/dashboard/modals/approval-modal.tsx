"use client";
import React, { useEffect, useMemo, useState } from "react";

type Staff = { name: string; is_active: boolean };

export interface ApprovalModalProps {
  jobId: string;
  material?: string | null;
  onClose: () => void;
  onApproved: () => void; // parent removes job from list
}

export default function ApprovalModal({ jobId, material, onClose, onApproved }: ApprovalModalProps) {
  const [staff, setStaff] = useState<Staff[]>([]);
  const [loadingStaff, setLoadingStaff] = useState(false);
  const [staffName, setStaffName] = useState("");
  const [weightG, setWeightG] = useState<string>("");
  const [timeHours, setTimeHours] = useState<string>("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string>("");

  const rate = useMemo(() => {
    const mat = (material || "").toLowerCase();
    if (mat === "resin") return 0.2;
    return 0.1; // default filament
  }, [material]);

  const costPreview = useMemo(() => {
    const w = parseFloat(weightG);
    if (Number.isNaN(w) || w <= 0) return 3.0; // show minimum by default
    const raw = w * rate;
    return Math.max(3.0, Math.round(raw * 100) / 100);
  }, [weightG, rate]);

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

  const isValid = staffName.trim().length > 0 && !!weightG && !!timeHours && parseFloat(weightG) > 0 && parseFloat(timeHours) > 0;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!isValid) return;
    try {
      setSubmitting(true);
      setError("");
      const token = localStorage.getItem("token");
      const res = await fetch(`/api/v1/jobs/${jobId}/approve`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          staff_name: staffName,
          weight_g: parseFloat(weightG),
          time_hours: parseFloat(timeHours),
        }),
      });
      if (!res.ok) {
        const text = await res.text();
        throw new Error(text || "Failed to approve job");
      }
      onApproved();
      onClose();
    } catch (err) {
      setError("Approval failed. Please check inputs and try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <div className="relative bg-white w-full max-w-md rounded-xl shadow-lg border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Approve Job</h3>
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

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Weight (grams)</label>
              <input
                type="number"
                min="0"
                step="0.1"
                className="w-full border rounded-lg px-3 py-2 focus-ring"
                value={weightG}
                onChange={(e) => setWeightG(e.target.value)}
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Time (hours)</label>
              <input
                type="number"
                min="0"
                step="0.5"
                className="w-full border rounded-lg px-3 py-2 focus-ring"
                value={timeHours}
                onChange={(e) => setTimeHours(e.target.value)}
                required
              />
            </div>
          </div>

          <div className="bg-gray-50 border rounded-lg p-3 text-sm text-gray-700">
            Estimated cost: <span className="font-semibold">${" "}{costPreview.toFixed(2)}</span> ({material ? material : "Filament"} @ ${rate.toFixed(2)}/g, $3.00 min)
          </div>

          <div className="flex justify-end space-x-2 pt-2">
            <button type="button" onClick={onClose} className="px-4 py-2 rounded-lg border text-gray-700 hover:bg-gray-50 focus-ring btn-transition">
              Cancel
            </button>
            <button
              type="submit"
              disabled={!isValid || submitting}
              className="px-4 py-2 rounded-lg bg-green-600 text-white hover:bg-green-700 disabled:opacity-50 focus-ring btn-transition"
            >
              {submitting ? "Approving..." : "Approve"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}


