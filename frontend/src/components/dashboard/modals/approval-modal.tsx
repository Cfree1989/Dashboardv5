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
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [candidateFiles, setCandidateFiles] = useState<{ name: string; mtime: number }[]>([]);
  const [authoritativeFilename, setAuthoritativeFilename] = useState<string>("");
  const [showChooser, setShowChooser] = useState(false);
  const [rescanning, setRescanning] = useState(false);

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
    // Initial candidate fetch
    doRescan(false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function doRescan(forceShowChooser: boolean) {
    try {
      setRescanning(true);
      const token = localStorage.getItem("token");
      const res = await fetch(`/api/v1/jobs/${jobId}/candidate-files`, { headers: { Authorization: `Bearer ${token}` } });
      if (!res.ok) return;
      const data = await res.json();
      // Support both shapes: files_detailed (preferred) or files (strings or objects)
      const raw = (data?.files_detailed ?? data?.files ?? []) as any[];
      let parsed: { name: string; mtime: number }[];
      if (raw.length > 0 && typeof raw[0] === 'string') {
        parsed = (raw as string[]).map((name) => ({ name, mtime: 0 }));
      } else {
        parsed = (raw as { name?: string; mtime?: number }[])
          .filter((f) => typeof f?.name === 'string')
          .map((f) => ({ name: f.name as string, mtime: typeof f.mtime === 'number' ? f.mtime : 0 }));
      }
      // Let server recommendation drive selection if present; otherwise keep same or newest
      const recommended: string | undefined = data?.recommended;
      if (recommended && parsed.some(f => f.name === recommended)) {
        parsed.sort((a, b) => (a.name === recommended ? -1 : b.name === recommended ? 1 : b.mtime - a.mtime));
      } else {
        parsed.sort((a, b) => b.mtime - a.mtime);
      }
      setCandidateFiles(parsed);
      if (parsed.length > 0) {
        // Keep current selection if still present, otherwise pick newest
        const keep = parsed.find((f) => f.name === authoritativeFilename);
        setAuthoritativeFilename(keep ? keep.name : (recommended && parsed.some(f => f.name === recommended) ? recommended : parsed[0].name));
      }
      if (forceShowChooser && parsed.length > 1) setShowChooser(true);
    } catch {
      // non-fatal
    } finally {
      setRescanning(false);
    }
  }

  const isValid = staffName.trim().length > 0 && !!weightG && !!timeHours && parseFloat(weightG) > 0 && parseFloat(timeHours) > 0;

  async function doApprove() {
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
          authoritative_filename: authoritativeFilename || undefined,
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
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Approve Job</h3>
        {error && (
          <div className="mb-3 text-sm text-red-600" role="alert">{error}</div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {!!candidateFiles.length && (
            <div className="space-y-1">
              <div className="flex items-center justify-between">
                <div className="text-sm text-gray-700">
                  Using file: <span className="font-medium">{authoritativeFilename || candidateFiles[0]?.name}</span>
                </div>
                <div className="flex items-center gap-3">
                  <button
                    type="button"
                    onClick={() => doRescan(true)}
                    className="text-xs text-blue-600 hover:text-blue-800 disabled:opacity-50"
                    disabled={rescanning}
                  >
                    {rescanning ? 'Scanning…' : 'Detect newer saves'}
                  </button>
                  {candidateFiles.length > 1 && !showChooser && (
                    <button
                      type="button"
                      onClick={() => setShowChooser(true)}
                      className="text-xs text-blue-600 hover:text-blue-800"
                    >
                      Choose different file…
                    </button>
                  )}
                </div>
              </div>
              {showChooser && candidateFiles.length > 1 && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Select file</label>
                  <select
                    className="w-full border rounded-lg px-3 py-2 focus-ring"
                    value={authoritativeFilename}
                    onChange={(e) => setAuthoritativeFilename(e.target.value)}
                  >
                    {candidateFiles.map((f) => (
                      <option key={f.name} value={f.name}>{f.name}</option>
                    ))}
                  </select>
                  <div className="mt-1">
                    <button
                      type="button"
                      onClick={() => setShowChooser(false)}
                      className="text-xs text-gray-500 hover:text-gray-700"
                    >
                      Hide file chooser
                    </button>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">Newest files appear first.</p>
                </div>
              )}
            </div>
          )}
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
              <label htmlFor="weightG" className="block text-sm font-medium text-gray-700 mb-1">Weight (grams)</label>
              <input
                id="weightG"
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
              <label htmlFor="timeHours" className="block text-sm font-medium text-gray-700 mb-1">Time (hours)</label>
              <input
                id="timeHours"
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
          <p className="text-xs text-gray-500 mt-2">You will be asked to confirm on the next step.</p>
        </form>
      </div>
      {confirmOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="absolute inset-0 bg-black/40" onClick={() => setConfirmOpen(false)} />
          <div className="relative bg-white w-full max-w-sm rounded-xl shadow-lg border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-1">Are you sure?</h3>
            <p className="text-sm text-gray-600 mb-4">This will send an approval email and move the job to Pending.</p>
            <div className="flex justify-end space-x-2">
              <button onClick={() => setConfirmOpen(false)} className="px-4 py-2 rounded-lg border text-gray-700 hover:bg-gray-50 focus-ring btn-transition">Cancel</button>
              <button onClick={doApprove} className="px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 focus-ring btn-transition">Yes, approve</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}


